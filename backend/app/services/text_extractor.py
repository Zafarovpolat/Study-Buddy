# backend/app/services/text_extractor.py - ЗАМЕНИ ПОЛНОСТЬЮ
import os
import re
from pathlib import Path


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
                raise ValueError("PDF не содержит текста (возможно, сканированный документ)")
            
            return text
            
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
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_parts.append(" | ".join(row_text))
            
            text = "\n\n".join(text_parts)
            
            if not text.strip():
                raise ValueError("DOCX не содержит текста")
            
            return text
            
        except KeyError:
            raise ValueError("Файл повреждён или имеет неправильный формат. Попробуйте пересохранить документ в Word.")
        except Exception as e:
            error_msg = str(e)
            if "relationship" in error_msg.lower() or "KeyError" in error_msg:
                raise ValueError("Файл повреждён или защищён. Откройте в Word и сохраните как .docx")
            raise ValueError(f"Ошибка чтения DOCX: {error_msg}")
    
    @staticmethod
    async def extract_from_doc(file_path: str) -> str:
        """Извлечь текст из старого формата DOC (Word 97-2003)"""
        raise ValueError(
            "Формат .doc (Word 97-2003) не поддерживается. "
            "Откройте файл в Microsoft Word и сохраните как .docx"
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
                        return text
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        raise ValueError("Не удалось прочитать файл. Проверьте кодировку.")
    
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
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content([
                {
                    "mime_type": mime_type,
                    "data": base64.b64encode(image_data).decode('utf-8')
                },
                """Извлеки весь текст с этого изображения. 
                Если это фото доски, конспекта или документа - распознай весь текст.
                Сохрани структуру. Если текста нет - напиши "Текст не обнаружен"."""
            ])
            
            text = response.text.strip()
            
            if not text or "не обнаружен" in text.lower():
                raise ValueError("Не удалось распознать текст на изображении")
            
            return text
            
        except Exception as e:
            raise ValueError(f"Ошибка распознавания: {str(e)}")
    
    @classmethod
    async def extract(cls, file_path: str, material_type: str) -> str:
        """Универсальный метод извлечения текста"""
        
        if not os.path.exists(file_path):
            raise ValueError("Файл не найден")
        
        if os.path.getsize(file_path) == 0:
            raise ValueError("Файл пустой")
        
        # ВАЖНО: Определяем тип по расширению файла, НЕ по material_type!
        ext = Path(file_path).suffix.lower()
        
        ext_to_extractor = {
            '.pdf': cls.extract_from_pdf,
            '.docx': cls.extract_from_docx,
            '.doc': cls.extract_from_doc,      # Отдельный обработчик!
            '.txt': cls.extract_from_txt,
            '.jpg': cls.extract_from_image,
            '.jpeg': cls.extract_from_image,
            '.png': cls.extract_from_image,
            '.webp': cls.extract_from_image,
            '.gif': cls.extract_from_image,
        }
        
        extractor = ext_to_extractor.get(ext)
        
        if not extractor:
            raise ValueError(f"Формат {ext} не поддерживается. Используйте PDF, DOCX, TXT или изображения.")
        
        print(f"📂 Extracting from: {file_path} (ext: {ext})")
        
        text = await extractor(file_path)
        
        # Очистка
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text