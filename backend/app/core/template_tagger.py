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

    if "{{ event_title }}" in all_text and "{{ discussion }}" in all_text:
        # Already tagged
        return

    def replace_in_para(p):
        txt = p.text.strip()
        if not txt:
            return

        def set_text(new_txt, bold=None):
            if p.runs:
                p.runs[0].text = new_txt
                if bold is not None:
                    p.runs[0].bold = bold
                for r in p.runs[1:]:
                    r.text = ""
            else:
                p.text = new_txt

        # Event title
        if "BRICKS TO BOT" in txt or ("Event:" in txt and any(w in txt for w in ["AI", "Workshop", "Civil"])):
            set_text("Event: “{{ event_title }}”", bold=True)

        # Date
        elif "Date:" in txt and ("20th August" in txt or "Date: -" in txt):
            set_text("Date: - {{ event_date }}")

        # Participants
        elif "Participants:" in txt and ("23" in txt or "Participants: -" in txt):
            set_text("Participants: - {{ participant_count }}")

        # Department
        elif "Department:" in txt and "All" in txt:
            set_text("Department: {{ department }}")

        # Targeted Audience
        elif "Targeted Audience:" in txt:
            set_text("Targeted Audience: {{ target_audience }}")

        # Speakers
        elif "1. Mr. Nishant Dakua" in txt or "1. Mr.Nishant Dakua" in txt:
            set_text("{{ speakers_block }}")
        elif "2. Mr.Suraj Yadav" in txt or "2. Mr. Suraj Yadav" in txt:
            set_text("")

        # Introduction
        elif "On 20th August 2026" in txt or "APSIT AIML Club, successfully conducted" in txt:
            set_text("{{ introduction }}")

        # Discussion
        elif "The session commenced with a warm welcome" in txt:
            set_text("{{ discussion }}")
        elif any(phrase in txt for phrase in [
            "introduced participants to the AI Stack",
            "focused on Prompt Engineering",
            "connected with Civil Engineering",
            "hands-on demonstrations",
            "Mentimeter quiz competition",
            "Doubts of students were addressed"
        ]):
            set_text("")

        # Conclusion
        elif "successfully introduced students" in txt or "workshop successfully introduced" in txt:
            set_text("{{ conclusion }}")

        # Photo Captions
        elif "Speakers introducing the concepts" in txt:
            set_text("{{ photo_1_caption }}")
        elif "Students engaging in the session" in txt:
            set_text("{{ photo_2_caption }}")
        elif "Speaker solving doubts" in txt:
            set_text("{{ photo_3_caption }}")
        elif "Winner of Mentimeter" in txt:
            set_text("{{ photo_4_caption }}")

    # Process all body paragraphs
    for p in doc.paragraphs:
        replace_in_para(p)

    # Process all table cells (in case metadata or captions are in tables)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    replace_in_para(p)

    doc.save(str(template_path))
    print(f"[SUCCESS] Report template automatically tagged with Jinja2 placeholders at: {template_path}")
