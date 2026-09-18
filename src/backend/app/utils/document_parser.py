"""
Document parser for extracting text from various formats (.md, .pdf).
Sprint 4 PART B: PDF support.
"""
from pathlib import Path
import io
import logging

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)

# Supported formats
SUPPORTED_FORMATS = {".md", ".txt", ".pdf"}
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class DocumentParseError(Exception):
    """Raised when document parsing fails."""
    pass


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file content.
    
    Args:
        file_content: Raw PDF bytes
        
    Returns:
        Extracted text as string
        
    Raises:
        DocumentParseError: If PDF parsing fails
    """
    if not PDF_AVAILABLE:
        raise DocumentParseError(
            "PDF support not available. Install pypdf: pip install pypdf"
        )
    
    try:
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        
        if len(reader.pages) == 0:
            raise DocumentParseError("PDF file is empty (0 pages)")
        
        # Extract text from all pages
        text_parts = []
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text_parts.append(page_text)
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {e}")
                continue
        
        if not text_parts:
            raise DocumentParseError(
                "No text could be extracted from PDF. "
                "File may be image-based or corrupted."
            )
        
        full_text = "\n\n".join(text_parts)
        logger.info(f"Extracted {len(full_text)} characters from {len(reader.pages)} pages")
        
        return full_text
        
    except DocumentParseError:
        raise
    except Exception as e:
        logger.error(f"PDF parsing failed: {e}", exc_info=True)
        raise DocumentParseError(f"Failed to parse PDF: {str(e)}")


def extract_text_from_markdown(file_content: bytes) -> str:
    """
    Extract text from markdown/text file content.
    
    Args:
        file_content: Raw file bytes
        
    Returns:
        Decoded text as string
        
    Raises:
        DocumentParseError: If decoding fails
    """
    try:
        # Try UTF-8 first (most common)
        return file_content.decode("utf-8")
    except UnicodeDecodeError:
        # Fallback to latin-1 (never fails)
        try:
            return file_content.decode("latin-1")
        except Exception as e:
            raise DocumentParseError(f"Failed to decode text file: {str(e)}")


def parse_document(
    filename: str,
    file_content: bytes,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES
) -> str:
    """
    Parse document and extract text based on file extension.
    
    Args:
        filename: Original filename (used for extension detection)
        file_content: Raw file bytes
        max_size_bytes: Maximum allowed file size
        
    Returns:
        Extracted text as string
        
    Raises:
        DocumentParseError: If parsing fails or validation fails
    """
    # Validate file size
    file_size = len(file_content)
    if file_size > max_size_bytes:
        raise DocumentParseError(
            f"File too large: {file_size / 1024 / 1024:.1f}MB "
            f"(max: {max_size_bytes / 1024 / 1024:.0f}MB)"
        )
    
    if file_size == 0:
        raise DocumentParseError("File is empty (0 bytes)")
    
    # Detect file type by extension
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in SUPPORTED_FORMATS:
        raise DocumentParseError(
            f"Unsupported file format: {file_ext}. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    # Parse based on format
    logger.info(f"Parsing {file_ext} file: {filename} ({file_size} bytes)")
    
    if file_ext == ".pdf":
        text = extract_text_from_pdf(file_content)
    else:  # .md, .txt
        text = extract_text_from_markdown(file_content)
    
    # Validate extracted text
    if not text or not text.strip():
        raise DocumentParseError(
            f"No text content extracted from {filename}"
        )
    
    logger.info(f"Successfully extracted {len(text)} characters from {filename}")
    return text
