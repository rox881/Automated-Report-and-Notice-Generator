"""
create_report_template.py
=========================
Reads the original report.docx uploaded by the user, locates the specific
paragraphs containing hardcoded sample content, and replaces them with
Jinja2-style {{ field_key }} tags that docxtpl can substitute at generation time.

Run from the project root:
    python scripts/create_report_template.py

Requires: python-docx  (pip install python-docx)
"""

import docx
from docx.oxml.ns import qn
import copy
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
SRC_PATH      = r"C:\Users\Gaurav\.gemini\antigravity\brain\49dcb98d-aa68-418e-81ec-39b8a774f8cc\.user_uploaded\media_1790843695792.docx"
TEMPLATE_PATH = r"templates\report\template.docx"

# ── Helper: print all paragraphs with index ────────────────────────────────────
def inspect(doc):
    for i, p in enumerate(doc.paragraphs):
        print(f"[{i:3d}] style={p.style.name!r:30s}  text={p.text[:80]!r}")

# ── Helper: clear all runs in a paragraph and set new text ──────────────────────
def set_paragraph_text(para, text, bold=False, font_size=None):
    """Clears all runs, then adds a single run with the given text."""
    for run in para.runs:
        run.text = ""
    if para.runs:
        run = para.runs[0]
    else:
        run = para.add_run()
    run.text = text
    run.bold = bold
    if font_size:
        run.font.size = docx.shared.Pt(font_size)

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print(f"Loading source: {SRC_PATH}")
    doc = docx.Document(SRC_PATH)

    print("\n── All paragraphs (inspect before editing) ──")
    inspect(doc)

    # ──────────────────────────────────────────────────────────────────────────
    # INSTRUCTIONS TO USER:
    # ─────────────────────
    # After running the inspect above, note the paragraph INDICES that contain:
    #   • The event title  ("BRICKS TO BOT" or similar)
    #   • The date line    ("Date:" ...)
    #   • Participants line
    #   • Department line
    #   • Target audience line
    #   • Speakers line(s)
    #   • Introduction text block
    #   • Discussion text block(s)
    #   • Conclusion text block
    #   • Photo caption 1, 2, 3, 4
    #
    # Then update the index constants below and re-run.
    # ──────────────────────────────────────────────────────────────────────────

    # ── CONFIGURE THESE INDICES AFTER RUNNING INSPECT ────────────────────────
    # Defaults are based on the uploaded "BRICKS TO BOT" report document.
    # Adjust if your document differs.

    IDX_EVENT_TITLE      = None   # e.g. paragraph that says "BRICKS TO BOT – ..."
    IDX_DATE             = None   # paragraph that says "Date: 20th August 2026"
    IDX_PARTICIPANTS     = None   # paragraph that says "No. of Participants: 23"
    IDX_DEPARTMENT       = None   # paragraph that says "Department: ..."
    IDX_TARGET_AUDIENCE  = None   # paragraph that says "Targeted Audience: ..."
    IDX_SPEAKERS         = None   # paragraph that lists speaker names
    IDX_INTRODUCTION     = None   # paragraph(s) for Introduction text
    IDX_DISCUSSION_START = None   # first paragraph of Discussion
    IDX_DISCUSSION_END   = None   # last  paragraph of Discussion (inclusive)
    IDX_CONCLUSION       = None   # paragraph for Conclusion text
    IDX_CAPTION_1        = None   # Photo 1 caption paragraph
    IDX_CAPTION_2        = None   # Photo 2 caption paragraph
    IDX_CAPTION_3        = None   # Photo 3 caption paragraph
    IDX_CAPTION_4        = None   # Photo 4 caption paragraph

    # ── After setting indices above, remove the guard below ──────────────────
    if any(v is None for v in [
        IDX_EVENT_TITLE, IDX_DATE, IDX_PARTICIPANTS, IDX_SPEAKERS,
        IDX_INTRODUCTION, IDX_DISCUSSION_START, IDX_DISCUSSION_END,
        IDX_CONCLUSION,
    ]):
        print("\n" + "="*70)
        print("STEP 1 COMPLETE — Inspect output printed above.")
        print("Now set the IDX_* constants in this script to the correct")
        print("paragraph indices and run again.")
        print("="*70)
        return

    # ── Apply tags ────────────────────────────────────────────────────────────
    paras = doc.paragraphs

    # Event Title
    set_paragraph_text(paras[IDX_EVENT_TITLE], "{{ event_title }}", bold=True)

    # Date
    set_paragraph_text(paras[IDX_DATE], "Date: {{ event_date }}")

    # Participants
    set_paragraph_text(paras[IDX_PARTICIPANTS], "No. of Participants: {{ participant_count }}")

    # Department (optional — only set if the paragraph exists)
    if IDX_DEPARTMENT is not None:
        set_paragraph_text(paras[IDX_DEPARTMENT], "Department: {{ department }}")

    # Target Audience (optional)
    if IDX_TARGET_AUDIENCE is not None:
        set_paragraph_text(paras[IDX_TARGET_AUDIENCE], "Targeted Audience: {{ target_audience }}")

    # Speakers
    set_paragraph_text(paras[IDX_SPEAKERS], "{{ speakers_block }}")

    # Introduction (single paragraph tag — docxtpl will expand newlines)
    set_paragraph_text(paras[IDX_INTRODUCTION], "{{ introduction }}")

    # Discussion — collapse all discussion paragraphs into first one
    # Set the first paragraph as the tag, clear the rest
    set_paragraph_text(paras[IDX_DISCUSSION_START], "{{ discussion }}")
    for i in range(IDX_DISCUSSION_START + 1, IDX_DISCUSSION_END + 1):
        set_paragraph_text(paras[i], "")

    # Conclusion
    set_paragraph_text(paras[IDX_CONCLUSION], "{{ conclusion }}")

    # Photo captions
    if IDX_CAPTION_1 is not None:
        set_paragraph_text(paras[IDX_CAPTION_1], "{{ photo_1_caption }}")
    if IDX_CAPTION_2 is not None:
        set_paragraph_text(paras[IDX_CAPTION_2], "{{ photo_2_caption }}")
    if IDX_CAPTION_3 is not None:
        set_paragraph_text(paras[IDX_CAPTION_3], "{{ photo_3_caption }}")
    if IDX_CAPTION_4 is not None:
        set_paragraph_text(paras[IDX_CAPTION_4], "{{ photo_4_caption }}")

    # Save
    doc.save(TEMPLATE_PATH)
    print(f"\n✅ Template saved to: {TEMPLATE_PATH}")

    # Verify tags exist
    verify_doc = docx.Document(TEMPLATE_PATH)
    all_text = "\n".join(p.text for p in verify_doc.paragraphs)
    tags = ["event_title", "event_date", "participant_count", "speakers_block",
            "introduction", "discussion", "conclusion"]
    print("\n── Verification ──")
    for tag in tags:
        found = f"{{{{{tag}}}}}" in all_text
        print(f"  {{{{ {tag} }}}}  →  {'✅ FOUND' if found else '❌ MISSING'}")


if __name__ == "__main__":
    main()
