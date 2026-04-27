import io

def extract_text(file_obj) -> str:
    filename = (file_obj.filename or '').lower()
    data     = file_obj.read()

    if filename.endswith('.pdf'):
        return _from_pdf(data)
    elif filename.endswith('.docx'):
        return _from_docx(data)
    elif filename.endswith('.doc'):
        raise ValueError('.doc format not supported. Please save as .docx or PDF.')
    else:
        try:
            return data.decode('utf-8')
        except Exception:
            return data.decode('latin-1', errors='ignore')


def _from_pdf(data: bytes) -> str:
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
        return '\n'.join(parts)
    except ImportError:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        return '\n'.join(p.extract_text() or '' for p in reader.pages)


def _from_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
