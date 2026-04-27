from weasyprint import HTML, CSS


def generate_pdf(resume_text: str, user_name: str = 'Resume') -> bytes:
    html = _build_html(resume_text)
    return HTML(string=html).write_pdf(stylesheets=[CSS(string=_css())])


def _build_html(text: str) -> str:
    lines    = text.strip().split('\n')
    body     = ''
    in_ul    = False

    for line in lines:
        s = line.strip()
        if not s:
            if in_ul:
                body += '</ul>'
                in_ul = False
            body += '<div class="sp"></div>'
            continue

        if s.isupper() and len(s) > 3:
            if in_ul:
                body += '</ul>'
                in_ul = False
            body += f'<div class="sh">{s}</div>'
            continue

        if s.startswith(('•', '-', '*', '·')):
            if not in_ul:
                body += '<ul>'
                in_ul = True
            body += f'<li>{s.lstrip("•-*· ").strip()}</li>'
            continue

        if in_ul:
            body += '</ul>'
            in_ul = False

        if len(s) < 80 and '|' not in s and s == s.title():
            body += f'<div class="et">{s}</div>'
        else:
            body += f'<p>{s}</p>'

    if in_ul:
        body += '</ul>'

    return f'<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>{body}</body></html>'


def _css() -> str:
    return '''
@page { size: A4; margin: 15mm 14mm; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 10.5pt; color: #111; line-height: 1.52; }
.sh { font-size: 9.5pt; font-weight: bold; text-transform: uppercase; letter-spacing: .07em; border-bottom: 1.5pt solid #111; padding-bottom: 2pt; margin: 10pt 0 6pt; }
.et { font-weight: bold; font-size: 10.5pt; margin: 4pt 0 2pt; }
p  { font-size: 10pt; margin: 2pt 0; color: #222; }
ul { padding-left: 13pt; margin: 2pt 0 4pt; }
li { font-size: 10pt; color: #222; margin-bottom: 2pt; }
.sp { height: 4pt; }
'''
