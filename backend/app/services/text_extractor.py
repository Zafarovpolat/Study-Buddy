# backend/app/services/text_extractor.py - ЗАМЕНИ ПОЛНОСТЬЮ
import os
import re
from pathlib import Path


def clean_text_for_db(text: str) -> str:
    """Очищает текст от символов, несовместимых с PostgreSQL UTF-8"""
    if not text:
        return ""
    
    # Удаляем null-байты (главная причина ошибки!)
    text = text.replace('\x00', '')
    
    # Удаляем другие проблемные control characters (кроме \n, \r, \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Заменяем суррогатные пары на пробелы
    text = text.encode('utf-8', errors='replace').decode('utf-8')
    
    return text


class TextExtractor:
    """Извлечение текста из разных форматов файлов"""
    
    @staticmethod
    async def extract_from_pdf(file_path: str) -> str:
        """Извлечь текст из PDF"""
        try:
            import pypdf
            
            text_parts = []
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            text = "\n\n".join(text_parts)
            
            if not text.strip():
                raise ValueError("PDF не содержит текста")
            
            # ОЧИСТКА!
            return clean_text_for_db(text)
            
        except Exception as e:
            raise ValueError(f"Ошибка чтения PDF: {str(e)}")
    
    @staticmethod
    async def extract_from_docx(file_path: str) -> str:
        """Извлечь текст из DOCX"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text_parts = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        text_parts.append(" | ".join(row_text))
            
            text = "\n\n".join(text_parts)
            
            if not text.strip():
                raise ValueError("DOCX не содержит текста")
            
            # ОЧИСТКА!
            return clean_text_for_db(text)
            
        except KeyError:
            raise ValueError("Файл повреждён. Сохраните как .docx в Word")
        except Exception as e:
            if "relationship" in str(e).lower():
                raise ValueError("Файл повреждён. Сохраните как .docx в Word")
            raise ValueError(f"Ошибка чтения DOCX: {str(e)}")
    
    @staticmethod
    async def extract_from_doc(file_path: str) -> str:
        """Извлечь текст из DOC через Gemini OCR"""
        raise ValueError(
            "Формат .doc (Word 97-2003) не поддерживается. "
            "Откройте в Word → Файл → Сохранить как → выберите .docx"
        )
    
    @staticmethod
    async def extract_from_txt(file_path: str) -> str:
        """Извлечь текст из TXT"""
        encodings = ['utf-8', 'cp1251', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                    if text.strip():
                        # ОЧИСТКА!
                        return clean_text_for_db(text)
            except UnicodeDecodeError:
                continue
        
        raise ValueError("Не удалось прочитать файл")
    
    @staticmethod
    async def extract_from_image(file_path: str) -> str:
        """Извлечь текст из изображения через Gemini Vision"""
        try:
            import google.generativeai as genai
            from app.core.config import settings
            import base64
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            ext = Path(file_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp',
                '.gif': 'image/gif'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            print(f"🔍 Using model: {settings.GEMINI_MODEL}")
            
            response = model.generate_content([
                {
                    "mime_type": mime_type,
                    "data": base64.b64encode(image_data).decode('utf-8')
                },
                "Извлеки весь текст с изображения. Сохрани структуру. Только текст, без комментариев."
            ])
            
            text = response.text.strip()
            
            if not text or len(text) < 3:
                raise ValueError("Текст не распознан")
            
            # ОЧИСТКА!
            return clean_text_for_db(text)
            
        except Exception as e:
            error = str(e)
            if "404" in error or "not found" in error.lower():
                raise ValueError(f"Модель {settings.GEMINI_MODEL} недоступна")
            raise ValueError(f"Ошибка OCR: {error[:100]}")
    
    @classmethod
    async def extract(cls, file_path: str, material_type: str) -> str:
        """Универсальный метод"""
        
        if not os.path.exists(file_path):
            raise ValueError("Файл не найден")
        
        if os.path.getsize(file_path) == 0:
            raise ValueError("Файл пустой")
        
        ext = Path(file_path).suffix.lower()
        
        extractors = {
            '.pdf': cls.extract_from_pdf,
            '.docx': cls.extract_from_docx,
            '.doc': cls.extract_from_doc,
            '.txt': cls.extract_from_txt,
            '.jpg': cls.extract_from_image,
            '.jpeg': cls.extract_from_image,
            '.png': cls.extract_from_image,
            '.webp': cls.extract_from_image,
        }
        
        extractor = extractors.get(ext)
        
        if not extractor:
            raise ValueError(f"Формат {ext} не поддерживается")
        
        print(f"📂 Extracting {ext} from {file_path}")
        
        text = await extractor(file_path)
        
        # Финальная очистка
        text = clean_text_for_db(text)
        text = re.sub(r'\n{3,}', '\n\n', text.strip())
        
        return text