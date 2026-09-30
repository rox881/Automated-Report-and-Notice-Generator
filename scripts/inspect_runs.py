import docx

src_path = r"C:\Users\Gaurav\.gemini\antigravity\brain\49dcb98d-aa68-418e-81ec-39b8a774f8cc\.user_uploaded\media_1790774183369.docx"
doc = docx.Document(src_path)

for idx in [9, 14, 16, 17]:
    p = doc.paragraphs[idx]
    print(f"--- Paragraph {idx} ---")
    for r_idx, r in enumerate(p.runs):
        print(f"  Run {r_idx}: {repr(r.text)} | bold={r.bold} | italic={r.italic} | font={r.font.name} | size={r.font.size}")
