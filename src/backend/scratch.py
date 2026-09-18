import re
text = """# Heading 1

Some paragraph here.
With two lines.

- Bullet 1
- Bullet 2

## Heading 2

1. Numbered 1
2. Numbered 2
"""
for m in re.finditer(r'(?s)\S.*?(?=\n\s*\n|\Z)', text):
    print(repr(m.group(0)), m.span())
