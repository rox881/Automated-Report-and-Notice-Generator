# System Architecture: Report & Notice Generator

Reframed from the original design to match agreed decisions.

---

## What Changed from the Original Design

| Original (Claude's design) | Our Design |
| :--- | :--- |
| Next.js frontend | Vanilla HTML + CSS + JS |
| Redis session store | SQLite (no server needed) |
| Confidence scoring (high/medium/low) | Dropped — LLM returns value or `null` |
| LibreOffice layout check | Dropped — manual check by you |
| Claude SDK hardcoded | LLM-agnostic `client.py` (you plug in your SDK) |

---

## Pipeline: Part 1 — Intake & Confirmation

```
[Web UI — HTML/CSS/JS]
  User pastes raw context text
        │
        ▼
[Extract — LLM via client.py]
  Reads context + fields.json
  Returns field values or null
        │
        ▼
[Validate — Pydantic + Code]
  Required field missing? ──Yes──► [Ask User in UI]
        │                                  │
        No ◄──── User fills missing fields ┘
        │
        ▼
[Preview — UI inline table]
  User reviews all fields,
  edits any value, then confirms
        │
        ▼
[Session Store — SQLite]
  Confirmed fields saved to DB
  Both templates read from here
```

---

## Pipeline: Part 2 — Generation & Download

```
[SQLite — Confirmed Fields]
        │
        ▼
[Template Job]
  Notice first (Button A)
  Report second (Button B, unlocks after A)
        │
        ▼
[Field Formatter — core/formatter.py]
  Applies typed rules:
  • dates, speaker lists, title-case
  • Builds RichText objects where needed
        │
        ▼
[Fill Engine — docxtpl on a copy of template.docx]
  Replaces {{ tags }} in .docx copy
  Preserves all fonts, sizes, tables, photo slots
        │
        ▼
[Save to output/]
        │
        ▼
[Browser Download — .docx file]
```

---

## Directory Structure

```
Report Generator/
│
├── documents/                  # Specs and architecture (you are here)
│   ├── architecture.md
│   ├── notice-template.md
│   ├── report-template.md
│   └── ui-design.md
│
├── templates/                  # Source .docx files and field schemas
│   ├── notice/
│   │   ├── template.docx       # Pre-tagged with {{ field_key }}
│   │   └── fields.json         # Key, label, type, required, max_chars
│   └── report/
│       ├── template.docx
│       └── fields.json
│
├── backend/
│   ├── requirements.txt        # fastapi, uvicorn, pydantic, docxtpl, jinja2
│   └── app/
│       ├── main.py             # FastAPI app entry, mounts frontend static files
│       ├── config.py           # Reads .env (LLM_API_KEY, DB_PATH)
│       │
│       ├── api/routes/
│       │   ├── sessions.py     # POST /sessions (create + submit context)
│       │   ├── fields.py       # GET missing fields, POST user answers, confirm
│       │   ├── generate.py     # POST /generate/{notice|report}
│       │   └── files.py        # GET /download/{job_id}
│       │
│       ├── schemas/
│       │   ├── session.py      # Session, SessionStatus
│       │   ├── fields.py       # FieldSpec, FieldValue
│       │   └── jobs.py         # Job, JobStatus
│       │
│       ├── core/               # One function per pipeline stage
│       │   ├── extractor.py    # Build prompt → call LLM → parse JSON
│       │   ├── validator.py    # Required check, type check, max_chars
│       │   ├── gap_checker.py  # Return list of missing required fields
│       │   ├── formatter.py    # Typed rules + RichText for speakers list
│       │   ├── filler.py       # docxtpl render on a template copy
│       │   └── job_runner.py   # Notice then Report, status tracking
│       │
│       ├── llm/
│       │   ├── client.py       # complete(system, user) → str  ← you fill this
│       │   ├── schema_builder.py  # Converts fields.json → prompt field spec text
│       │   └── prompts/
│       │       ├── extract_system.md   # LLM system instructions
│       │       └── extract_user.md.j2  # Jinja2 user prompt template
│       │
│       ├── registry/
│       │   └── loader.py       # Loads all fields.json at startup, validates tags
│       │
│       ├── db/
│       │   ├── schema.sql      # Sessions, field_values, jobs tables
│       │   ├── connection.py   # SQLite connection helper
│       │   ├── sessions_repo.py
│       │   └── jobs_repo.py
│       │
│       ├── storage/
│       │   └── file_store.py   # Saves .docx to output/ with versioned filename
│       │
│       └── utils/
│           ├── errors.py       # Typed exceptions
│           └── formats.py      # Date, title-case, speaker list helpers
│
├── frontend/
│   ├── index.html              # Single page, all steps inline
│   ├── style.css               # ChatGPT-style dark sidebar + clean main area
│   └── app.js                  # Step switching, fetch calls to backend API
│
├── output/                     # Generated .docx files (gitignored)
├── .env.example                # LLM_API_KEY, LLM_MODEL, DB_PATH
└── README.md
```

---

## SQLite Tables

```sql
-- One row per user session
CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,
    context     TEXT NOT NULL,
    status      TEXT NOT NULL,  -- extracted | needs_input | confirmed
    created_at  TEXT NOT NULL
);

-- One row per field per session
CREATE TABLE field_values (
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    field_key   TEXT NOT NULL,
    value_json  TEXT,           -- string or JSON list
    source      TEXT NOT NULL,  -- 'llm' or 'user'
    PRIMARY KEY (session_id, field_key)
);

-- One row per document generation job
CREATE TABLE jobs (
    id           TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL REFERENCES sessions(id),
    template_id  TEXT NOT NULL, -- 'notice' or 'report'
    status       TEXT NOT NULL, -- pending | running | done | failed
    output_path  TEXT,
    error        TEXT,
    created_at   TEXT NOT NULL,
    finished_at  TEXT
);
```

---

## Key Design Principles

1. **LLM does one job only:** Extract field values from context. It returns a value or `null`. No formatting, no layout decisions.
2. **Formatting lives in the template:** Font sizes, bold, italic, photo placeholders — all in `.docx`. `docxtpl` fills tags and leaves everything else untouched.
3. **No confidence scoring:** Field is present → use it. Field is null + required → ask user. Simple binary.
4. **One shared session, two outputs:** Both Notice and Report read from the same SQLite session row. Fields shared between templates (like `event_title`, `speakers`) are entered once.
