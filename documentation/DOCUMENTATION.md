* [ ] 

# Project Documentation — Automated Report & Notice Generator

> ⚠️ **Status: Under Active Development**
> This project is actively being built and improved. Features, file structures, and flows described here reflect the current state and may evolve.

---

## What Is This?

This is a **web-based document generator** that turns raw event notes into properly formatted Word (`.docx`) files — either a **Notice** or an **Event Report** — in just a few clicks.

You paste in rough notes about an event (date, speakers, what happened, etc.), pick a document type, and the system uses AI to extract the right details and fill them into a ready-made Word template. If anything is missing, it asks you to fill it in before generating the final document.

**Think of it like this:**

> You give it rough notes → It reads and understands them with AI → Fills in a formatted Word document → You download it.

The current templates and branding (college name, club name, signatory names) use a specific institution's design as a working example/placeholder — these are straightforward to swap out for any other organisation.

---

## Tech Stack — What, Why, and How

| Technology                        | Role                                               | Why It Was Chosen                                                              |
| :-------------------------------- | :------------------------------------------------- | :----------------------------------------------------------------------------- |
| **Python + FastAPI**        | Backend web server & API                           | Fast, modern, easy to read; built-in data validation                           |
| **Groq API (LLM)**          | AI that reads notes and extracts/writes content    | Runs`llama-3.3-70b-versatile` model; fast and free-tier friendly             |
| **docxtpl**                 | Fills`.docx` Word templates with dynamic values  | Preserves all Word formatting — fonts, logos, tables — without touching them |
| **python-docx**             | Inspects and tags the`.docx` template at startup | Used to automatically inject`{{ placeholders }}` into the Word file once     |
| **SQLAlchemy + SQLite**     | Database for storing sessions and field values     | No external database server needed; single file`app.db`                      |
| **Pydantic**                | Validates incoming data shapes                     | Catches bad input early; auto-generates API docs                               |
| **Jinja2**                  | Assembles the AI prompt from a template            | Keeps prompts in clean`.md.j2` files — easy to edit without touching code   |
| **Vanilla HTML + CSS + JS** | Frontend (the web page you interact with)          | No heavy framework needed; simple, fast, works offline                         |
| **Uvicorn**                 | Runs the FastAPI server                            | Lightweight ASGI server; one command to start                                  |

---

## How the Pipeline Works — From Notes to Word Document

The system works in **two connected pipelines**.

### Pipeline 1 — Intake, Extraction & Confirmation

This is what happens from the moment you paste your notes to the moment you click "Generate".

```
User pastes raw event notes into the text box
              │
              ▼
    [Step 1] Create Session
    A unique session ID is created and the raw text is saved to SQLite.
              │
              ▼
    [Step 2] AI Extraction (Groq LLM)
    The LLM reads the notes and extracts structured field values
    (event title, date, speakers, participant count, etc.).
    For Report documents → it also generates Introduction, Discussion, Conclusion.
    Any field it cannot find → it returns null.
              │
              ▼
    [Step 3] Gap Check
    The system checks: are any REQUIRED fields still null?
         │
         ├── YES → Show "Missing Information" form (Step 2 in UI)
         │         User fills in the missing fields.
         │
         └── NO → Go straight to Review
              │
              ▼
    [Step 4] Review & Edit (Step 3 in UI)
    All extracted values shown in an editable table.
    For Reports: Introduction, Discussion, Conclusion shown in rich editors.
    User can directly edit any field, or click AI "Preset" buttons
    to reframe/rewrite a narrative section with a different style.
              │
              ▼
    [Step 5] Confirm
    User clicks "Confirm & Generate".
    All final field values are saved back to SQLite with source = 'user'.
    Session status is set to "confirmed".
```

### Pipeline 2 — Document Generation & Download

This happens in the background after the user clicks "Confirm & Generate".

```
    [Confirmed SQLite Session]
              │
              ▼
    [Background Job Created]
    A Job record is created in SQLite with status = "pending".
    A background task is launched (separate thread).
              │
              ▼
    [Formatter]
    Reads all field values from the DB.
    Applies typed formatting rules:
    • dates → DD/MM/YYYY format
    • speaker lists → numbered list as RichText
    • narrative fields → converted to docxtpl RichText objects
      (so **bold** and paragraph breaks work in Word)
              │
              ▼
    [Template Filler — docxtpl]
    Opens the .docx template file.
    Replaces every {{ tag }} with the formatted value.
    Saves a NEW copy to the output/ folder.
    The original template is NEVER modified.
              │
              ▼
    [Job Status: "done"]
    The frontend polls every 1.2 seconds asking "is the job done?"
    When done → a Download button appears.
              │
              ▼
    [User Downloads .docx]
    The file is streamed directly to the browser.
```

---

## File Structure — What Every File Does

```
Report Generator/
├── .env                    ← Your private API key lives here (not committed to git)
├── .env.example            ← Safe copy showing what keys are needed
├── README.md               ← Quick setup guide
│
├── documents/              ← All design & documentation files (you are here)
│   ├── DOCUMENTATION.md    ← This file
│   ├── architecture.md     ← Original architecture decisions & pipeline diagrams
│   ├── notice-template.md  ← Typography & field spec for the Notice document
│   ├── report-template.md  ← Typography & field spec for the Report document
│   └── ui-design.md        ← UI layout and visual design notes
│
├── templates/              ← Word templates and field definitions
│   ├── notice/
│   │   ├── template.docx   ← Pre-tagged Word file with {{ field }} placeholders
│   │   └── fields.json     ← Defines every field: key, label, type, required, max_chars
│   └── report/
│       ├── template.docx   ← Auto-tagged at startup if not already tagged
│       └── fields.json     ← Defines report fields including narrative sections
│
├── output/                 ← Generated .docx files land here (gitignored)
│
├── frontend/
│   ├── index.html          ← The single web page; contains all 4 UI steps inline
│   ├── style.css           ← Visual styling: dark sidebar, A4 preview pane, cards
│   └── app.js              ← All frontend logic: API calls, step navigation,
│                              live A4 preview, AI reframing, download polling
│
└── backend/
    ├── requirements.txt    ← All Python packages needed (install with pip)
    └── app/
        ├── main.py         ← App entry point; registers all routes; runs startup tasks
        ├── config.py       ← Reads .env file; resolves relative paths to absolute
        │
        ├── api/routes/     ← HTTP endpoints — the "doors" the frontend knocks on
        │   ├── sessions.py ← Create session, run extraction, reframe narrative,
        │   │                  get preview data, list history
        │   ├── fields.py   ← Get missing fields, submit user answers, confirm session
        │   ├── generate.py ← Kick off background document generation job,
        │   │                  check job status
        │   └── files.py    ← Stream the finished .docx file to the browser
        │
        ├── schemas/        ← Data shape definitions (what the API accepts/returns)
        │   ├── session.py  ← SessionCreate, SessionResponse, ReframeRequest shapes
        │   ├── fields.py   ← FieldSpec, MissingField, UserAnswers, FieldAnswer shapes
        │   └── jobs.py     ← JobResponse shape
        │
        ├── core/           ← The main brain — one file per pipeline stage
        │   ├── extractor.py      ← Calls the LLM with a built prompt; parses the
        │   │                        JSON response; sanitises null-like values;
        │   │                        triggers narrative synthesis for reports
        │   ├── gap_checker.py    ← Checks which required fields are still empty;
        │   │                        narrative fields (intro/discussion/conclusion)
        │   │                        are intentionally excluded from the gap check
        │   ├── formatter.py      ← Converts raw values to Word-ready format:
        │   │                        dates → DD/MM/YYYY, lists → numbered RichText,
        │   │                        **markdown bold** → Word bold via RichText
        │   ├── filler.py         ← Opens template.docx with docxtpl, renders all
        │   │                        {{ tags }}, and saves the output copy
        │   ├── job_runner.py     ← Runs inside a background thread; opens its own
        │   │                        fresh DB session; transitions job status
        │   │                        pending → running → done/failed
        │   └── template_tagger.py← On first startup, inspects report/template.docx;
        │                           if it still has hardcoded sample text, replaces it
        │                           with {{ event_title }}, {{ introduction }}, etc.
        │                           Runs only once; skipped if already tagged.
        │
        ├── llm/                  ← Everything related to talking to the AI
        │   ├── client.py         ← Single function `complete(system, user) → str`;
        │   │                        sends the two-part prompt to Groq; enforces
        │   │                        JSON-only response mode
        │   ├── schema_builder.py ← Converts the fields.json list into a plain-text
        │   │                        table that is injected into the extraction prompt
        │   └── prompts/
        │       ├── extract_system.md   ← System instructions for the extraction LLM call:
        │       │                          "Only use information from the context. Return null
        │       │                           if not found. Output valid JSON only."
        │       ├── extract_user.md.j2  ← Jinja2 template: slots in the field spec table
        │       │                          and the user's pasted context at runtime
        │       ├── report_synthesis.md ← System instructions for generating Introduction,
        │       │                          Discussion, Conclusion from event metadata
        │       └── reframe_prompt.md   ← System instructions for rewriting/reframing
        │                                  a single narrative section per user instruction
        │
        ├── registry/
        │   └── loader.py         ← At startup, reads every templates/*/fields.json into
        │                            an in-memory dictionary. Other parts of the app call
        │                            get_fields("notice") or get_fields("report") to get
        │                            the list of FieldSpec objects.
        │
        ├── db/                   ← Database layer
        │   ├── connection.py     ← Creates the SQLite engine and SessionLocal factory;
        │   │                        init_db() creates tables on first run
        │   ├── models.py         ← Three SQLAlchemy tables:
        │   │                        Session (id, context, status, created_at)
        │   │                        FieldValue (session_id, field_key, value_json, source)
        │   │                        Job (id, session_id, template_id, status, output_path,
        │   │                             error, created_at, finished_at)
        │   ├── sessions_repo.py  ← All DB read/write functions for sessions and field values
        │   └── jobs_repo.py      ← All DB read/write functions for generation jobs
        │
        ├── storage/
        │   └── file_store.py     ← Generates a unique, timestamped output file path
        │                            like output/report_a1b2c3d4_20261007_123456.docx
        │                            Creates the output/ folder if it doesn't exist
        │
        └── utils/
            └── errors.py         ← Custom exception types: ExtractionError,
                                     FillerError, RegistryError, ValidationError
```

---

## The Three Database Tables — Explained Simply

Think of the database like a filing cabinet with three drawers:

### 1. `sessions` — One row per "paste & generate" action

Stores the raw text you pasted and tracks where you are in the process (`extracted`, `needs_input`, or `confirmed`).

### 2. `field_values` — One row per extracted/entered value

Each field (like `event_title` or `speakers`) gets its own row. It also records whether the value came from the **LLM** (`source = 'llm'`) or was **typed by you** (`source = 'user'`). User-provided values always win.

### 3. `jobs` — One row per document generation attempt

Tracks each document being built in the background. Status moves: `pending → running → done` (or `failed` if something went wrong). Once `done`, it stores the path to the generated `.docx` file.

---

## How the AI Is Used — Two Separate Calls

The LLM (Groq's `llama-3.3-70b-versatile`) is used in two distinct, separate ways:

### Call 1 — Field Extraction

- **When:** When you click "Generate Notice" or "Generate Report" in Step 1.
- **What it does:** Reads your pasted text and extracts specific facts — date, title, speakers, participant count, etc. — based on the field list in `fields.json`.
- **Rule:** It is told *only* to extract what is already in your text. If a field is not mentioned, it must return `null`. It is not allowed to make things up.

### Call 2 — Narrative Synthesis (Report only)

- **When:** After field extraction, if the Introduction/Discussion/Conclusion are missing or too short (under 100 characters).
- **What it does:** Using the extracted metadata + your original pasted text, the LLM writes formal academic-style paragraphs for Introduction, Discussion, and Conclusion.
- **User control:** These can be further edited manually or reframed with AI "Preset" buttons in Step 3 (e.g., "More Formal", "Concise", "Expand Details").

### Call 3 — Section Reframing (on demand)

- **When:** User clicks an AI Preset chip or types a custom instruction in Step 3.
- **What it does:** Rewrites a single narrative section (Introduction, Discussion, or Conclusion) based on the instruction, while keeping the facts accurate.

---

## How `{{ placeholders }}` Get Into the Word Template

The Word templates work using **Jinja2-style tags** like `{{ event_title }}` or `{{ introduction }}`. Here's how they get there:

- **Notice template:** The `templates/notice/template.docx` already has all `{{ tags }}` pre-placed manually. It is never auto-modified.
- **Report template:** The `templates/report/template.docx` may start as a plain Word file with sample text. On first startup, `template_tagger.py` inspects it — if it doesn't already have `{{ event_title }}`, `{{ introduction }}`, etc., it **automatically replaces the sample text** with the proper tags and saves the file. This is a one-time operation.

When generating a document:

1. `docxtpl` opens the tagged `.docx` template.
2. It substitutes every `{{ key }}` with the real value.
3. It saves a **new copy** to `output/`. The original template is never touched during generation.

---

## What Happens When Bold Text Appears in the Report

The AI generates narratives using `**markdown bold**` syntax (e.g., `**Prompt Engineering**`). The system needs to convert this into *real* Word bold formatting — not just asterisk characters.

This is handled by `formatter.py → text_to_richtext()`:

1. It parses the text token by token.
2. `**text**` → added to Word as bold run.
3. `*text*` → added as italic run.
4. `\n\n` (blank line) → paragraph break in Word.

The result is a `docxtpl.RichText` object that Word understands natively.

---

## Session History (Sidebar)

The left sidebar shows past sessions. Each entry shows:

- The event title (if extracted) or "Session" as fallback.
- The date/time it was created.

Clicking a history entry **restores** that session directly to Step 3 (Review), so you can re-download or make edits without re-running the AI.

---

## Key Design Decisions

| Decision                                                 | Reasoning                                                                                                                                                  |
| :------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **SQLite instead of Redis/Postgres**               | No external services needed; single`app.db` file works for local use                                                                                     |
| **Background task for generation**                 | Generating a`.docx` can take a second or two — doing it in the background keeps the HTTP response instant and the UI responsive                         |
| **Separate `SessionLocal` for background tasks** | FastAPI's request-scoped DB session closes when the HTTP response is sent; the background thread needs its own fresh session to read committed data safely |
| **LLM only extracts — never formats**             | The LLM returns raw values or null. All formatting (date format, bold, line breaks) is handled in Python code — predictable and testable                  |
| **Narrative fields excluded from gap-check**       | Introduction/Discussion/Conclusion are AI-synthesised automatically; the user is never asked to write them manually in the "Missing Fields" form           |
| **Fields.json drives everything**                  | Adding a new field to a template only requires updating`fields.json` and the `.docx` template — no code changes needed                                |

---

*This documentation was written to reflect the current state of the project. As the project evolves, this file should be updated to match.*
