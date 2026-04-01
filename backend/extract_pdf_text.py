"""Extract text from PDF and save as .txt for AI paper generation testing."""
from pypdf import PdfReader

pdf_path = r"D:\2026上半年项目\2026年4月开发项目\police-training-platform\docs\公安网文件\刘校成\公安机关日常性训练体系梳理.pdf"
txt_path = r"D:\2026上半年项目\2026年4月开发项目\police-training-platform\docs\公安网文件\刘校成\公安机关日常性训练体系梳理.txt"

reader = PdfReader(pdf_path)
print(f"PDF 共 {len(reader.pages)} 页")

text_parts = []
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text:
        text_parts.append(f"--- 第 {i+1} 页 ---\n{text}")
    else:
        text_parts.append(f"--- 第 {i+1} 页 ---\n[无文本内容]")

full_text = "\n\n".join(text_parts)
with open(txt_path, "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"已提取 {len(full_text)} 字符，保存到: {txt_path}")
