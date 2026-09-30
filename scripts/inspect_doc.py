import docx

src_path = r"C:\Users\Gaurav\.gemini\antigravity\brain\49dcb98d-aa68-418e-81ec-39b8a774f8cc\.user_uploaded\media_1790774183369.docx"
doc = docx.Document(src_path)

print("Paragraphs:")
for i, p in enumerate(doc.paragraphs):
    if p.text.strip():
        print(f"P{i}: {repr(p.text)}")
