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
                except Exception as e:
                    print(f"❌ Text extraction failed: {e}")
                    raise
            
            content = material.raw_content
            if not content:
                raise ValueError("Нет контента для обработки")
            
            print(f"🤖 Generating AI outputs...")
            
            # 3. Генерация AI-контента
            results = await self._generate_all_outputs(content, material.title)
            
            # 4. Сохраняем результаты
            saved_count = 0
            for format_type, output_content in results.items():
                if output_content:
                    ai_output = AIOutput(
                        material_id=material.id,
                        format=OutputFormat(format_type),
                        content=output_content
                    )
                    self.db.add(ai_output)
                    saved_count += 1
            
            # 5. Финальный статус
            material.status = ProcessingStatus.COMPLETED
            await self.db.commit()
            
            print(f"✅ Processing complete! Saved {saved_count} outputs")
            
            return {
                "status": "success",
                "outputs": list(results.keys())
            }
            
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            print(traceback.format_exc())
            
            material.status = ProcessingStatus.FAILED
            await self.db.commit()
            
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _generate_all_outputs(
        self, 
        content: str, 
        title: str
    ) -> Dict[str, str]:
        """Генерация всех форматов"""
        results = {}
        
        # Генерируем по очереди с обработкой ошибок
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
                results[name] = await generator()
                print(f"  ✅ {name} done")
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