# backend/app/services/text_extractor.py - ЗАМЕНИ ПОЛНОСТЬЮ
from pypdf import PdfReader
from docx import Document
from pathlib import Path
import aiofiles

from app.services.ai_service import gemini_service


class TextExtractor:
    """Извлечение текста из различных форматов"""
    
    @staticmethod
    async def extract_from_pdf(file_path: str) -> str:
        """Извлечь текст из PDF"""
        text_parts = []
        
        try:
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    text_parts.append(f"--- Страница {page_num + 1} ---\n{text}")
        except Exception as e:
            raise ValueError(f"Ошибка чтения PDF: {str(e)}")
        
        if not text_parts:
            raise ValueError("Не удалось извлечь текст из PDF")
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    async def extract_from_docx(file_path: str) -> str:
        """Извлечь текст из DOCX"""
        try:
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            paragraphs.append(cell.text)
            
            return "\n\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Ошибка чтения DOCX: {str(e)}")
    
    @staticmethod
    async def extract_from_txt(file_path: str) -> str:
        """Прочитать текстовый файл"""
        encodings = ['utf-8', 'cp1251', 'latin-1']
        
        for encoding in encodings:
            try:
                async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                    return await f.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError("Не удалось прочитать файл")
    
    @staticmethod
    async def extract_from_image(file_path: str) -> str:
        """OCR: Извлечь текст из изображения через Gemini Vision"""
        try:
            text = await gemini_service.extract_text_from_image(file_path)
            
            if not text or len(text.strip()) < 10:
                raise ValueError("Не удалось распознать текст на изображении")
            
            return text.strip()
        except Exception as e:
            raise ValueError(f"Ошибка OCR: {str(e)}")
    
    @classmethod
    async def extract(cls, file_path: str, material_type: str) -> str:
        """Универсальный метод извлечения"""
        extractors = {
            'pdf': cls.extract_from_pdf,
            'docx': cls.extract_from_docx,
            'txt': cls.extract_from_txt,
            'image': cls.extract_from_image,
        }
        
        extractor = extractors.get(material_type)
        if not extractor:
            raise ValueError(f"Неподдерживаемый тип: {material_type}")
        
        text = await extractor(file_path)
        
        if not text or len(text.strip()) < 20:
            raise ValueError("Недостаточно текста для обработки")
        
        return text.strip()