import asyncio
from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Material, AIOutput, OutputFormat, ProcessingStatus
from app.services.text_extractor import TextExtractor
from app.services.ai_service import gemini_service
from app.core.config import settings

class ProcessingService:
    """Сервис обработки материалов"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process_material(self, material: Material) -> Dict[str, Any]:
        """Полная обработка материала"""
        try:
            # 1. Обновляем статус
            material.status = ProcessingStatus.PROCESSING
            await self.db.commit()
            
            # 2. Извлекаем текст если нужно
            if not material.raw_content and material.file_path:
                text = await TextExtractor.extract(
                    material.file_path,
                    material.material_type.value
                )
                material.raw_content = text
                await self.db.commit()
            
            content = material.raw_content
            if not content:
                raise ValueError("Нет контента для обработки")
            
            # 3. Параллельная генерация AI-контента
            results = await self._generate_all_outputs(content, material.title)
            
            # 4. Сохраняем результаты
            for format_type, output_content in results.items():
                if output_content:
                    ai_output = AIOutput(
                        material_id=material.id,
                        format=OutputFormat(format_type),
                        content=output_content
                    )
                    self.db.add(ai_output)
            
            # 5. Финальный статус
            material.status = ProcessingStatus.COMPLETED
            await self.db.commit()
            
            return {
                "status": "success",
                "outputs": list(results.keys())
            }
            
        except Exception as e:
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
        """Параллельная генерация всех форматов"""
        
        # Запускаем все генерации параллельно
        tasks = {
            "smart_notes": gemini_service.generate_smart_notes(content, title),
            "tldr": gemini_service.generate_tldr(content),
            "quiz": gemini_service.generate_quiz(content, num_questions=5),
            "glossary": gemini_service.generate_glossary(content),
            "flashcards": gemini_service.generate_flashcards(content, num_cards=10),
        }
        
        results = {}
        
        # Выполняем с обработкой ошибок для каждой задачи
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                print(f"Error generating {name}: {e}")
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
        
        # Генерируем нужный формат
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
        
        # Удаляем старый output если есть
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