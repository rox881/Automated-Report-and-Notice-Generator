"""
template_tagger.py
==================
Automatically inspects templates/report/template.docx and replaces hardcoded sample
text (from the original sample report) with Jinja2 placeholders ({{ event_title }}, etc.)
if they have not already been injected.
"""

from pathlib import Path
import docx

from app.config import settings


def ensure_report_template_tagged(template_path: Path = None):
    """
    Checks if templates/report/template.docx contains {{ event_title }}.
    If not, it tags all metadata, narrative sections, and photo captions so that
    docxtpl can replace them dynamically for every new event report.
    """
    if template_path is None:
        template_path = Path(settings.templates_dir) / "report" / "template.docx"

    if not template_path.exists():
        return

    doc = docx.Document(str(template_path))

    # Check if already tagged
    all_text = " ".join(p.text for p in doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                all_text += " " + cell.text

    if (
        "{{ event_title }}" in all_text
        and "{{ introduction }}" in all_text
        and "{{ discussion }}" in all_text
        and "{{ conclusion }}" in all_text
        and "{{ speakers_block }}" in all_text
    ):
        # Already tagged
        return

    def set_text(p, new_txt, bold=None):
        if p.runs:
            p.runs[0].text = new_txt
            if bold is not None:
                p.runs[0].bold = bold
            for r in p.runs[1:]:
                r.text = ""
        else:
            p.text = new_txt

    current_section = "metadata"
    intro_tagged = False
    discussion_tagged = False
    conclusion_tagged = False

    # Process body paragraphs using section-aware tracking
    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue

        lower_clean = txt.lower().strip("*").rstrip(":- \t").strip("*")

        # Detect section headings
        if lower_clean == "introduction":
            current_section = "introduction"
            continue
        elif lower_clean == "discussion":
            current_section = "discussion"
            continue
        elif lower_clean == "conclusion":
            current_section = "conclusion"
            continue
        elif lower_clean.startswith("photo") or "photo gallery" in lower_clean:
            current_section = "photos"
            continue

        # Tag paragraphs based on current section
        if current_section == "metadata":
            # Event title (only inside metadata block before narrative headers)
            if (
                "BRICKS TO BOT" in txt
                or ("Event:" in txt and any(w in txt for w in ["AI", "Workshop", "Civil"]))
                or "{{ event_title }}" in txt
            ):
                set_text(p, "Event: “{{ event_title }}”", bold=True)

            # Date
            elif "Date:" in txt and ("20th August" in txt or "Date: -" in txt or "{{ event_date }}" in txt):
                set_text(p, "Date: - {{ event_date }}")

            # Participants
            elif "Participants:" in txt and ("23" in txt or "Participants: -" in txt or "{{ participant_count }}" in txt):
                set_text(p, "Participants: - {{ participant_count }}")

            # Department
            elif "Department:" in txt and ("All" in txt or "{{ department }}" in txt):
                set_text(p, "Department: {{ department }}")

            # Targeted Audience
            elif "Targeted Audience:" in txt:
                set_text(p, "Targeted Audience: {{ target_audience }}")

            # Speakers
            elif "1. Mr. Nishant Dakua" in txt or "1. Mr.Nishant Dakua" in txt or "{{ speakers_block }}" in txt:
                set_text(p, "{{ speakers_block }}")
            elif "2. Mr.Suraj Yadav" in txt or "2. Mr. Suraj Yadav" in txt:
                set_text(p, "")

        elif current_section == "introduction":
            if not intro_tagged:
                set_text(p, "{{ introduction }}", bold=False)
                intro_tagged = True
            else:
                set_text(p, "")

        elif current_section == "discussion":
            if not discussion_tagged:
                set_text(p, "{{ discussion }}", bold=False)
                discussion_tagged = True
            else:
                set_text(p, "")

        elif current_section == "conclusion":
            if not conclusion_tagged:
                set_text(p, "{{ conclusion }}", bold=False)
                conclusion_tagged = True
            else:
                set_text(p, "")

        elif current_section == "photos":
            if "Speakers introducing the concepts" in txt or "{{ photo_1_caption }}" in txt:
                set_text(p, "{{ photo_1_caption }}")
            elif "Students engaging in the session" in txt or "{{ photo_2_caption }}" in txt:
                set_text(p, "{{ photo_2_caption }}")
            elif "Speaker solving doubts" in txt or "{{ photo_3_caption }}" in txt:
                set_text(p, "{{ photo_3_caption }}")
            elif "Winner of Mentimeter" in txt or "{{ photo_4_caption }}" in txt:
                set_text(p, "{{ photo_4_caption }}")

    # Process all table cells (in case metadata or captions are in tables)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    txt = p.text.strip()
                    if not txt:
                        continue
                    if "Speakers introducing the concepts" in txt or "{{ photo_1_caption }}" in txt:
                        set_text(p, "{{ photo_1_caption }}")
                    elif "Students engaging in the session" in txt or "{{ photo_2_caption }}" in txt:
                        set_text(p, "{{ photo_2_caption }}")
                    elif "Speaker solving doubts" in txt or "{{ photo_3_caption }}" in txt:
                        set_text(p, "{{ photo_3_caption }}")
                    elif "Winner of Mentimeter" in txt or "{{ photo_4_caption }}" in txt:
                        set_text(p, "{{ photo_4_caption }}")

    doc.save(str(template_path))
    print(f"[SUCCESS] Report template automatically tagged with Jinja2 placeholders at: {template_path}")
