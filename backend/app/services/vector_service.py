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

# Размер chunk в символах
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


class VectorService:
    """Сервис для vector search (RAG)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
    
    def _split_into_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Разбивает текст на chunks с перекрытием"""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + CHUNK_SIZE
            
            # Пытаемся разбить по предложению
            if end < len(text):
                # Ищем конец предложения
                for sep in ['. ', '.\n', '! ', '? ', '\n\n']:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > CHUNK_SIZE // 2:
                        end = start + last_sep + len(sep)
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "chunk_index": chunk_index,
                    "char_start": start,
                    "char_end": end
                })
                chunk_index += 1
            
            start = end - CHUNK_OVERLAP
            if start < 0:
                start = end
        
        return chunks
    
    def _get_embedding_sync(self, text: str) -> List[float]:
        """Синхронное получение embedding"""
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Асинхронное получение embedding"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_embedding_sync, text)
    
    async def index_material(self, material_id: UUID, user_id: UUID, content: str) -> int:
        """Индексирует материал — создаёт chunks с embeddings"""
        if not content or len(content.strip()) < 50:
            return 0
        
        # Удаляем старые chunks
        await self.db.execute(
            text("DELETE FROM text_chunks WHERE material_id = :material_id"),
            {"material_id": str(material_id)}
        )
        
        # Разбиваем на chunks
        chunks = self._split_into_chunks(content)
        
        print(f"📊 Indexing {len(chunks)} chunks for material {material_id}")
        
        # Получаем embeddings и сохраняем
        for chunk in chunks:
            try:
                embedding = await self._get_embedding(chunk["content"])
                
                await self.db.execute(
                    text("""
                        INSERT INTO text_chunks (material_id, user_id, content, chunk_index, embedding)
                        VALUES (:material_id, :user_id, :content, :chunk_index, :embedding)
                    """),
                    {
                        "material_id": str(material_id),
                        "user_id": str(user_id),
                        "content": chunk["content"],
                        "chunk_index": chunk["chunk_index"],
                        "embedding": embedding
                    }
                )
            except Exception as e:
                print(f"⚠️ Failed to index chunk {chunk['chunk_index']}: {e}")
        
        await self.db.commit()
        print(f"✅ Indexed {len(chunks)} chunks")
        
        return len(chunks)
    
    async def search(
        self, 
        user_id: UUID, 
        query: str, 
        limit: int = 5,
        material_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Поиск по векторам"""
        # Получаем embedding запроса
        query_embedding = await self._get_embedding(query)
        
        # Поиск похожих chunks
        if material_id:
            # Поиск в конкретном материале
            result = await self.db.execute(
                text("""
                    SELECT 
                        tc.id,
                        tc.material_id,
                        tc.content,
                        tc.chunk_index,
                        m.title as material_title,
                        1 - (tc.embedding <=> :embedding) as similarity
                    FROM text_chunks tc
                    JOIN materials m ON m.id = tc.material_id
                    WHERE tc.material_id = :material_id
                    ORDER BY tc.embedding <=> :embedding
                    LIMIT :limit
                """),
                {
                    "embedding": query_embedding,
                    "material_id": str(material_id),
                    "limit": limit
                }
            )
        else:
            # Поиск по всем материалам пользователя
            result = await self.db.execute(
                text("""
                    SELECT 
                        tc.id,
                        tc.material_id,
                        tc.content,
                        tc.chunk_index,
                        m.title as material_title,
                        1 - (tc.embedding <=> :embedding) as similarity
                    FROM text_chunks tc
                    JOIN materials m ON m.id = tc.material_id
                    WHERE tc.user_id = :user_id
                    ORDER BY tc.embedding <=> :embedding
                    LIMIT :limit
                """),
                {
                    "embedding": query_embedding,
                    "user_id": str(user_id),
                    "limit": limit
                }
            )
        
        rows = result.fetchall()
        
        return [
            {
                "id": str(row.id),
                "material_id": str(row.material_id),
                "material_title": row.material_title,
                "content": row.content,
                "chunk_index": row.chunk_index,
                "similarity": float(row.similarity)
            }
            for row in rows
        ]
    
    async def ask_library(self, user_id: UUID, question: str) -> Dict[str, Any]:
        """Спроси свою библиотеку — RAG"""
        # Находим релевантные chunks
        chunks = await self.search(user_id, question, limit=5)
        
        if not chunks:
            return {
                "answer": "У вас пока нет проиндексированных материалов. Загрузите материалы и попробуйте снова.",
                "sources": []
            }
        
        # Формируем контекст
        context_parts = []
        for chunk in chunks:
            context_parts.append(
                f"[Из материала: {chunk['material_title']}]\n{chunk['content']}"
            )
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Генерируем ответ
        prompt = f"""Ты — умный ассистент для учёбы. Отвечай на вопрос пользователя, 
используя ТОЛЬКО информацию из предоставленного контекста.

Контекст из материалов пользователя:
{context}

Вопрос: {question}

Правила:
1. Отвечай только на основе контекста
2. Если информации недостаточно — скажи об этом
3. Указывай из какого материала информация
4. Будь конкретен и полезен

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
                "answer": f"Ошибка генерации ответа: {str(e)}",
                "sources": []
            }