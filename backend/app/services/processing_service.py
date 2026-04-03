# backend/app/services/processing_service.py
import asyncio
import re
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from app.models import Material, AIOutput, OutputFormat, ProcessingStatus
from app.services.text_extractor import TextExtractor
from app.services.ai_service import gemini_service
from app.utils.text import clean_text_for_db


class ProcessingService:
    """Сервис обработки материалов"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_material(self, material: Material) -> Dict[str, Any]:
        """Полная обработка материала"""
        print(f"📄 Processing material: {material.id} ({material.material_type})")

        error_message = None
        content = None  # Сохраняем для индексации

        try:
            # 1. Обновляем статус
            material.status = ProcessingStatus.PROCESSING
            await self.db.commit()

            # 2. Извлекаем текст если нужно
            if not material.raw_content and material.file_path:
                print(f"📖 Extracting text from: {material.file_path}")
                try:
                    text = await TextExtractor.extract(
                        material.file_path, material.material_type
                    )
                    # ОЧИСТКА ТЕКСТА!
                    text = clean_text_for_db(text)
                    material.raw_content = text
                    await self.db.commit()
                    print(f"✅ Extracted {len(text)} characters")
                except ValueError as e:
                    error_message = str(e)
                    raise
                except Exception as e:
                    error_message = f"Не удалось прочитать файл: {str(e)}"
                    raise

            content = material.raw_content

            # Очистка на случай если raw_content был передан напрямую
            if content:
                content = clean_text_for_db(content)
                if content != material.raw_content:
                    material.raw_content = content
                    await self.db.commit()

            if not content:
                error_message = "Файл не содержит текста или пустой"
                raise ValueError(error_message)

            # Проверяем минимальную длину
            if len(content.strip()) < 50:
                error_message = (
                    "Слишком мало текста для обработки (минимум 50 символов)"
                )
                raise ValueError(error_message)

            print(f"🤖 Generating AI outputs for {len(content)} chars...")

            # 3. Генерация AI-контента
            results = await self._generate_all_outputs(content, material.title)

            # 4. Проверяем что хоть что-то сгенерировалось
            successful_outputs = {k: v for k, v in results.items() if v}

            if not successful_outputs:
                error_message = (
                    "AI не смог обработать материал. Попробуйте другой файл."
                )
                raise ValueError(error_message)

            # 5. Сохраняем результаты (с очисткой!)
            for format_type, output_content in successful_outputs.items():
                ai_output = AIOutput(
                    material_id=material.id,
                    format=format_type,
                    content=clean_text_for_db(output_content),
                )
                self.db.add(ai_output)

            # 6. Финальный статус
            material.status = ProcessingStatus.COMPLETED
            await self.db.commit()

            print(f"✅ Processing complete! Saved {len(successful_outputs)} outputs")

            # 7. АВТОИНДЕКСАЦИЯ для vector search (RAG)
            await self._index_for_vector_search(material, content)

            return {"status": "success", "outputs": list(successful_outputs.keys())}

        except Exception as e:
            final_error = error_message or str(e)
            print(f"❌ Processing failed: {final_error}")
            print(traceback.format_exc())

            # Rollback текущей транзакции перед новым коммитом
            try:
                await self.db.rollback()
            except:
                pass

            material.status = ProcessingStatus.FAILED
            if not material.raw_content:
                material.raw_content = f"[ОШИБКА] {final_error}"

            try:
                await self.db.commit()
            except Exception as commit_error:
                print(f"❌ Failed to commit error status: {commit_error}")
                await self.db.rollback()

            return {"status": "error", "error": final_error}

    async def _index_for_vector_search(self, material: Material, content: str) -> None:
        """Индексация материала для vector search (RAG)"""
        try:
            from app.services.vector_service import VectorService

            vector_service = VectorService(self.db)
            chunks_count = await vector_service.index_material(
                material_id=material.id, user_id=material.user_id, content=content
            )
            print(
                f"📊 Vector indexed: {chunks_count} chunks for material {material.id}"
            )
        except Exception as e:
            # Не критичная ошибка — материал всё равно обработан
            print(f"⚠️ Vector indexing failed (non-critical): {e}")

    async def _generate_all_outputs(self, content: str, title: str) -> Dict[str, str]:
        """Генерация всех форматов ПАРАЛЛЕЛЬНО через asyncio.gather()"""
        results = {}

        # Ограничиваем длину контента для API
        max_length = 50000
        if len(content) > max_length:
            print(f"⚠️ Content too long ({len(content)}), truncating to {max_length}")
            content = (
                content[:max_length]
                + "\n\n[... текст обрезан из-за большого размера ...]"
            )

        async def generate_with_cleanup(name: str, coro):
            try:
                result = await coro
                if result and len(result.strip()) > 10:
                    return name, clean_text_for_db(result), None
                return name, None, f"{name} returned empty"
            except Exception as e:
                return name, None, str(e)

        # Запускаем все 5 генераций ПАРАЛЛЕЛЬНО
        tasks = [
            generate_with_cleanup(
                "smart_notes", gemini_service.generate_smart_notes(content, title)
            ),
            generate_with_cleanup("tldr", gemini_service.generate_tldr(content)),
            generate_with_cleanup("quiz", gemini_service.generate_quiz(content, 10)),
            generate_with_cleanup(
                "glossary", gemini_service.generate_glossary(content)
            ),
            generate_with_cleanup(
                "flashcards", gemini_service.generate_flashcards(content, 10)
            ),
        ]

        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for item in completed:
            if isinstance(item, Exception):
                print(f"  ⚠️ Unexpected error: {item}")
                continue
            name, result, error = item
            if result:
                results[name] = result
                print(f"  ✅ {name} done ({len(result)} chars)")
            else:
                print(f"  ⚠️ {name} failed: {error}")
                results[name] = None

        return results

    async def regenerate_output(
        self, material: Material, output_format: str
    ) -> AIOutput:
        """Перегенерация конкретного формата"""
        content = material.raw_content
        if not content:
            raise ValueError("Нет контента для обработки")

        if content.startswith("[ОШИБКА]"):
            raise ValueError("Материал не был обработан. Загрузите файл заново.")

        # Очистка контента
        content = clean_text_for_db(content)

        # Используем строки вместо констант OutputFormat
        generators = {
            "smart_notes": lambda: gemini_service.generate_smart_notes(
                content, material.title
            ),
            "tldr": lambda: gemini_service.generate_tldr(content),
            "quiz": lambda: gemini_service.generate_quiz(content),
            "glossary": lambda: gemini_service.generate_glossary(content),
            "flashcards": lambda: gemini_service.generate_flashcards(content),
        }

        generator = generators.get(output_format)
        if not generator:
            raise ValueError(f"Неизвестный формат: {output_format}")

        output_content = await generator()

        # ОЧИСТКА результата!
        output_content = clean_text_for_db(output_content)

        # Удаляем старый
        from sqlalchemy import delete

        await self.db.execute(
            delete(AIOutput).where(
                AIOutput.material_id == material.id, AIOutput.format == output_format
            )
        )

        # Создаём новый
        ai_output = AIOutput(
            material_id=material.id, format=output_format, content=output_content
        )
        self.db.add(ai_output)
        await self.db.commit()
        await self.db.refresh(ai_output)

        return ai_output
