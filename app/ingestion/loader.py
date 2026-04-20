from io import BytesIO

from docx import Document
from markdown_it import MarkdownIt
from pypdf import PdfReader


def load_document(content_bytes: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        pdf_reader = PdfReader(BytesIO(content_bytes))
        text = "\n".join(page.extract_text() for page in pdf_reader.pages)
        return text
    
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(BytesIO(content_bytes))
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text
    
    if mime_type == "text/markdown":
        md = MarkdownIt()
        tokens = md.parse(content_bytes.decode("utf-8"))
        text = " ".join(token.content for token in tokens if token.content)
        return text
    
    if mime_type == "text/plain":
        return content_bytes.decode("utf-8")
    
    raise ValueError(f"Unsupported mime type: {mime_type}")