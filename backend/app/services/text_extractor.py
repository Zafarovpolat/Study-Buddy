# backend/app/services/text_extractor.py - ЗАМЕНИ ПОЛНОСТЬЮ
import os
from typing import Optional
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
            
            # Также извлекаем текст из таблиц
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
            
        except KeyError as e:
            # Файл повреждён или неправильный формат
            raise ValueError(f"Файл повреждён или имеет неправильный формат. Попробуйте пересохранить документ в Word.")
        except Exception as e:
            error_msg = str(e)
            if "relationship" in error_msg.lower():
                raise ValueError("Файл повреждён или защищён. Попробуйте открыть в Word и сохранить заново.")
            raise ValueError(f"Ошибка чтения DOCX: {error_msg}")
    
    @staticmethod
    async def extract_from_doc(file_path: str) -> str:
        """Извлечь текст из старого формата DOC"""
        try:
            # Пробуем antiword если установлен
            import subprocess
            result = subprocess.run(
                ['antiword', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        try:
            # Пробуем textract
            import textract
            text = textract.process(file_path).decode('utf-8')
            if text.strip():
                return text
        except:
            pass
        
        raise ValueError(
            "Формат .doc (старый Word) не поддерживается напрямую. "
            "Пожалуйста, откройте файл в Word и сохраните как .docx"
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
        
        raise ValueError("Не удалось прочитать текстовый файл. Проверьте кодировку.")
    
    @staticmethod
    async def extract_from_image(file_path: str) -> str:
        """Извлечь текст из изображения через Gemini Vision"""
        try:
            import google.generativeai as genai
            from app.core.config import settings
            import base64
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Читаем изображение
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # Определяем MIME тип
            ext = Path(file_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp',
                '.gif': 'image/gif'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            
            # Используем Gemini Vision
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content([
                {
                    "mime_type": mime_type,
                    "data": base64.b64encode(image_data).decode('utf-8')
                },
                """Извлеки весь текст с этого изображения. 
                Если это фото доски, конспекта или документа - распознай весь текст.
                Сохрани структуру и форматирование насколько возможно.
                Если текста нет - напиши "Текст не обнаружен".
                Отвечай только извлечённым текстом, без комментариев."""
            ])
            
            text = response.text.strip()
            
            if not text or "текст не обнаружен" in text.lower():
                raise ValueError("Не удалось распознать текст на изображении")
            
            return text
            
        except Exception as e:
            error_msg = str(e)
            if "API" in error_msg or "key" in error_msg.lower():
                raise ValueError("Ошибка API для распознавания изображений")
            raise ValueError(f"Ошибка распознавания изображения: {error_msg}")
    
    @classmethod
    async def extract(cls, file_path: str, material_type: str) -> str:
        """Универсальный метод извлечения текста"""
        
        if not os.path.exists(file_path):
            raise ValueError(f"Файл не найден: {file_path}")
        
        # Проверяем размер файла
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("Файл пустой")
        
        extractors = {
            'pdf': cls.extract_from_pdf,
            'docx': cls.extract_from_docx,
            'doc': cls.extract_from_doc,
            'txt': cls.extract_from_txt,
            'image': cls.extract_from_image,
        }
        
        extractor = extractors.get(material_type.lower())
        
        if not extractor:
            raise ValueError(f"Неподдерживаемый тип файла: {material_type}")
        
        try:
            text = await extractor(file_path)
            
            # Очистка текста
            text = text.strip()
            
            # Убираем множественные пробелы и переносы
            import re
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text)
            
            return text
            
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Ошибка извлечения текста: {str(e)}")