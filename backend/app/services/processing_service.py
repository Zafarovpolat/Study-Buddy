# backend/app/services/processing_service.py - ЗАМЕНИ ПОЛНОСТЬЮ
import asyncio
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from app.models import Material, AIOutput, OutputFormat, ProcessingStatus
from app.services.text_extractor import TextExtractor
from app.services.ai_service import gemini_service


class ProcessingService:
    """Сервис обработки материалов"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process_material(self, material: Material) -> Dict[str, Any]:
        """Полная обработка материала"""
        print(f"📄 Processing material: {material.id} ({material.material_type.value})")
        
        error_message = None
        
        try:
            # 1. Обновляем статус
            material.status = ProcessingStatus.PROCESSING
            await self.db.commit()
            
            # 2. Извлекаем текст если нужно
            if not material.raw_content and material.file_path:
                print(f"📖 Extracting text from: {material.file_path}")
                try:
                    text = await TextExtractor.extract(
                        material.file_path,
                        material.material_type.value
                    )
                    material.raw_content = text
                    await self.db.commit()
                    print(f"✅ Extracted {len(text)} characters")
                except ValueError as e:
                    # Понятная ошибка от TextExtractor
                    error_message = str(e)
                    raise
                except Exception as e:
                    error_message = f"Не удалось прочитать файл: {str(e)}"
                    raise
            
            content = material.raw_content
            if not content:
                error_message = "Файл не содержит текста или пустой"
                raise ValueError(error_message)
            
            # Проверяем минимальную длину
            if len(content.strip()) < 50:
                error_message = "Слишком мало текста для обработки (минимум 50 символов)"
                raise ValueError(error_message)
            
            print(f"🤖 Generating AI outputs for {len(content)} chars...")
            
            # 3. Генерация AI-контента
            results = await self._generate_all_outputs(content, material.title)
            
            # 4. Проверяем что хоть что-то сгенерировалось
            successful_outputs = {k: v for k, v in results.items() if v}
            
            if not successful_outputs:
                error_message = "AI не смог обработать материал. Попробуйте другой файл."
                raise ValueError(error_message)
            
            # 5. Сохраняем результаты
            for format_type, output_content in successful_outputs.items():
                ai_output = AIOutput(
                    material_id=material.id,
                    format=OutputFormat(format_type),
                    content=output_content
                )
                self.db.add(ai_output)
            
            # 6. Финальный статус
            material.status = ProcessingStatus.COMPLETED
            await self.db.commit()
            
            print(f"✅ Processing complete! Saved {len(successful_outputs)} outputs")
            
            return {
                "status": "success",
                "outputs": list(successful_outputs.keys())
            }
            
        except Exception as e:
            final_error = error_message or str(e)
            print(f"❌ Processing failed: {final_error}")
            print(traceback.format_exc())
            
            material.status = ProcessingStatus.FAILED
            # Сохраняем сообщение об ошибке в raw_content если он пустой
            if not material.raw_content:
                material.raw_content = f"[ОШИБКА] {final_error}"
            
            await self.db.commit()
            
            return {
                "status": "error",
                "error": final_error
            }
    
    async def _generate_all_outputs(
        self, 
        content: str, 
        title: str
    ) -> Dict[str, str]:
        """Генерация всех форматов"""
        results = {}
        
        # Ограничиваем длину контента для API
        max_length = 50000  # ~50k символов
        if len(content) > max_length:
            print(f"⚠️ Content too long ({len(content)}), truncating to {max_length}")
            content = content[:max_length] + "\n\n[... текст обрезан из-за большого размера ...]"
        
        generators = [
            ("smart_notes", lambda: gemini_service.generate_smart_notes(content, title)),
            ("tldr", lambda: gemini_service.generate_tldr(content)),
            ("quiz", lambda: gemini_service.generate_quiz(content, 5)),
            ("glossary", lambda: gemini_service.generate_glossary(content)),
            ("flashcards", lambda: gemini_service.generate_flashcards(content, 10)),
        ]
        
        for name, generator in generators:
            try:
                print(f"  📝 Generating {name}...")
                result = await generator()
                if result and len(result.strip()) > 10:
                    results[name] = result
                    print(f"  ✅ {name} done ({len(result)} chars)")
                else:
                    print(f"  ⚠️ {name} returned empty")
                    results[name] = None
            except Exception as e:
                print(f"  ❌ {name} failed: {e}")
                results[name] = None
        
        return results
    
    async def regenerate_output(
        self, 
        material: Material, 
        output_format: OutputFormat
    ) -> AIOutput:
        """Перегенерация конкретного формата"""
        content = material.raw_content
        if not content:
            raise ValueError("Нет контента для обработки")
        
        # Убираем сообщение об ошибке если оно там
        if content.startswith("[ОШИБКА]"):
            raise ValueError("Материал не был обработан. Загрузите файл заново.")
        
        generators = {
            OutputFormat.SMART_NOTES: lambda: gemini_service.generate_smart_notes(content, material.title),
            OutputFormat.TLDR: lambda: gemini_service.generate_tldr(content),
            OutputFormat.QUIZ: lambda: gemini_service.generate_quiz(content),
            OutputFormat.GLOSSARY: lambda: gemini_service.generate_glossary(content),
            OutputFormat.FLASHCARDS: lambda: gemini_service.generate_flashcards(content),
        }
        
        generator = generators.get(output_format)
        if not generator:
            raise ValueError(f"Неизвестный формат: {output_format}")
        
        output_content = await generator()
        
        # Удаляем старый
        from sqlalchemy import delete
        await self.db.execute(
            delete(AIOutput).where(
                AIOutput.material_id == material.id,
                AIOutput.format == output_format
            )
        )
        
        # Создаём новый
        ai_output = AIOutput(
            material_id=material.id,
            format=output_format,
            content=output_content
        )
        self.db.add(ai_output)
        await self.db.commit()
        await self.db.refresh(ai_output)
        
        return ai_output