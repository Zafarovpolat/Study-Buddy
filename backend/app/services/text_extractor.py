import fitz  # PyMuPDF
from docx import Document
from pathlib import Path
from typing import Optional
import aiofiles
import io

class TextExtractor:
    """Извлечение текста из различных форматов"""
    
    @staticmethod
    async def extract_from_pdf(file_path: str) -> str:
        """Извлечь текст из PDF"""
        text_parts = []
        
        try:
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"--- Страница {page_num + 1} ---\n{text}")
            doc.close()
        except Exception as e:
            raise ValueError(f"Ошибка чтения PDF: {str(e)}")
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    async def extract_from_docx(file_path: str) -> str:
        """Извлечь текст из DOCX"""
        try:
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Ошибка чтения DOCX: {str(e)}")
    
    @staticmethod
    async def extract_from_txt(file_path: str) -> str:
        """Прочитать текстовый файл"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except UnicodeDecodeError:
            # Пробуем другую кодировку
            async with aiofiles.open(file_path, 'r', encoding='cp1251') as f:
                return await f.read()
    
    @staticmethod
    async def extract_from_image(file_path: str) -> str:
        """OCR для изображений (опционально - требует tesseract)"""
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(file_path)
            # Пробуем русский + английский
            text = pytesseract.image_to_string(image, lang='rus+eng')
            return text.strip()
        except ImportError:
            raise ValueError("pytesseract не установлен. Установи: apt-get install tesseract-ocr tesseract-ocr-rus")
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
        
        if not text or len(text.strip()) < 50:
            raise ValueError("Не удалось извлечь достаточно текста из файла")
        
        return text.strip()