# backend/app/services/vector_service.py
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from app.core.config import settings

_executor = ThreadPoolExecutor(max_workers=2)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


class VectorService:
    """Сервис для vector search (RAG)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
    
    def _split_into_chunks(self, text_content: str) -> List[Dict[str, Any]]:
        """Разбивает текст на chunks с перекрытием"""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text_content):
            end = start + CHUNK_SIZE
            
            if end < len(text_content):
                for sep in ['. ', '.\n', '! ', '? ', '\n\n']:
                    last_sep = text_content[start:end].rfind(sep)
                    if last_sep > CHUNK_SIZE // 2:
                        end = start + last_sep + len(sep)
                        break
            
            chunk_text = text_content[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "chunk_index": chunk_index,
                })
                chunk_index += 1
            
            start = end - CHUNK_OVERLAP
            if start < 0:
                start = end
        
        return chunks
    
    def _get_embedding_sync(self, text_content: str) -> List[float]:
        """Синхронное получение embedding"""
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text_content,
            task_type="retrieval_document"
        )
        return result['embedding']
    
    async def _get_embedding(self, text_content: str) -> List[float]:
        """Асинхронное получение embedding"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_embedding_sync, text_content)
    
    async def index_material(self, material_id: UUID, user_id: UUID, content: str) -> int:
        """Индексирует материал — создаёт chunks с embeddings"""
        if not content or len(content.strip()) < 50:
            return 0
        
        # Удаляем старые chunks
        await self.db.execute(
            text("DELETE FROM text_chunks WHERE material_id = :material_id"),
            {"material_id": str(material_id)}
        )
        
        chunks = self._split_into_chunks(content)
        print(f"📊 Indexing {len(chunks)} chunks for material {material_id}")
        
        indexed = 0
        for chunk in chunks:
            try:
                embedding = await self._get_embedding(chunk["content"])
                
                # Сохраняем как ARRAY (без pgvector)
                await self.db.execute(
                    text("""
                        INSERT INTO text_chunks (material_id, content, chunk_index, embedding)
                        VALUES (:material_id, :content, :chunk_index, :embedding)
                    """),
                    {
                        "material_id": str(material_id),
                        "content": chunk["content"],
                        "chunk_index": chunk["chunk_index"],
                        "embedding": embedding  # PostgreSQL ARRAY
                    }
                )
                indexed += 1
            except Exception as e:
                print(f"⚠️ Failed to index chunk {chunk['chunk_index']}: {e}")
        
        await self.db.commit()
        print(f"✅ Indexed {indexed}/{len(chunks)} chunks")
        
        return indexed
    
    async def search(
        self, 
        user_id: UUID, 
        query: str, 
        limit: int = 5,
        material_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Поиск по векторам (cosine similarity без pgvector)"""
        query_embedding = await self._get_embedding(query)
        
        if material_id:
            # Поиск в конкретном материале
            result = await self.db.execute(
                text("""
                    SELECT 
                        tc.id,
                        tc.material_id,
                        tc.content,
                        tc.chunk_index,
                        tc.embedding,
                        m.title as material_title
                    FROM text_chunks tc
                    JOIN materials m ON m.id = tc.material_id
                    WHERE tc.material_id = :material_id
                      AND tc.embedding IS NOT NULL
                """),
                {"material_id": str(material_id)}
            )
        else:
            # Поиск по всем материалам пользователя (через JOIN с materials)
            result = await self.db.execute(
                text("""
                    SELECT 
                        tc.id,
                        tc.material_id,
                        tc.content,
                        tc.chunk_index,
                        tc.embedding,
                        m.title as material_title
                    FROM text_chunks tc
                    JOIN materials m ON m.id = tc.material_id
                    WHERE m.user_id = :user_id
                      AND tc.embedding IS NOT NULL
                """),
                {"user_id": str(user_id)}
            )
        
        rows = result.fetchall()
        
        # Вычисляем cosine similarity в Python
        results_with_similarity = []
        for row in rows:
            if row.embedding:
                similarity = self._cosine_similarity(query_embedding, row.embedding)
                results_with_similarity.append({
                    "id": str(row.id),
                    "material_id": str(row.material_id),
                    "material_title": row.material_title,
                    "content": row.content,
                    "chunk_index": row.chunk_index,
                    "similarity": similarity
                })
        
        # Сортируем по similarity и берём top N
        results_with_similarity.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results_with_similarity[:limit]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Вычисляет cosine similarity между двумя векторами"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def ask_library(self, user_id: UUID, question: str) -> Dict[str, Any]:
        """Спроси свою библиотеку — RAG"""
        chunks = await self.search(user_id, question, limit=5)
        
        if not chunks:
            return {
                "answer": "У вас пока нет проиндексированных материалов. Загрузите материалы и попробуйте снова.",
                "sources": []
            }
        
        context_parts = []
        for chunk in chunks:
            context_parts.append(
                f"[Из материала: {chunk['material_title']}]\n{chunk['content']}"
            )
        
        context = "\n\n---\n\n".join(context_parts)
        
        prompt = f"""Ты — умный ассистент для учёбы. Отвечай на вопрос, используя ТОЛЬКО информацию из контекста.

Контекст из материалов:
{context}

Вопрос: {question}

Правила:
1. Отвечай только на основе контекста
2. Если информации нет — скажи об этом
3. Укажи из какого материала информация
4. Будь конкретен

Ответ:"""

        try:
            from app.services.ai_service import gemini_service
            answer = await gemini_service._generate_async(prompt)
            
            return {
                "answer": answer,
                "sources": [
                    {
                        "material_id": chunk["material_id"],
                        "material_title": chunk["material_title"],
                        "similarity": chunk["similarity"]
                    }
                    for chunk in chunks
                ]
            }
        except Exception as e:
            print(f"❌ RAG error: {e}")
            return {
                "answer": f"Ошибка: {str(e)}",
                "sources": []
            }