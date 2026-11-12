# Notice Template Specification & Formatting Guide

Single-page Notice document with fixed and dynamic fields, including typography and font sizing rules.

---

## 1. Typography & Formatting Rules

| Element | Font Family | Font Size | Style | Alignment |
| :--- | :--- | :--- | :--- | :--- |
| **Department Header** | Times New Roman / Calibri | **12 pt** | Bold | Centered |
| **Metadata Line** *(Academic Year & Date)* | Times New Roman / Calibri | **12 pt** | Bold | Left & Right Justified |
| **Title ("Notice")** | Times New Roman / Calibri | **16 pt** | Bold | Centered |
| **Body Paragraph** | Times New Roman / Calibri | **14 pt** | Regular (Line spacing 1.25) | Justified |
| **Session Title (in Body)** | Times New Roman / Calibri | **14 pt** | Bold | Inline |
| **Speaker List** | Times New Roman / Calibri | **14 pt** | Bulleted (Names in Bold) | Left (hanging indent) |
| **Signatures** | Times New Roman / Calibri | **13 pt** | Bold | Left & Right Columns |
| **Footer** *(AI-ML CLUB \| APSIT)* | Times New Roman / Calibri | **11 pt** | Regular / Bold | Right |

---

## 2. Static Elements (Do NOT Change)

- **Header Banner:** College Crest, A. P. Shah Institute of Technology text, AIML Club Logo.
- **Department:** Department of Computer Science & Engineering (Artificial Intelligence & Machine Learning).
- **Title:** "Notice".
- **Audience:** "All AIML Club Learners are hereby informed that a session on...".
- **Signatories:**
  - `Prof. Vijesh Nair` — Departmental Coordinator
  - `Dr. Jaya Gupta` — Head of Department
- **Footer:** `AI-ML CLUB | APSIT`.

---

## 3. Dynamic Fields (`{{ field_key }}`)

| Field Key | Label | Type | Example |
| :--- | :--- | :--- | :--- |
| `academic_year` | Academic Year | text | `2026-27` |
| `notice_date` | Notice Date | date / text | `19/08/2026` |
| `session_title` | Session Title | text | `BRICKS TO BOT – AI Workshop for Civil Engineering Students` |
| `event_date` | Event Date | text | `20th august` |
| `event_time` | Event Time | text | `1:00 PM - 3:30 PM` |
| `venue` | Venue / Room | text | `Lab 404` |
| `speakers` | List of Speakers (N items) | list | `["Mr. Nishant Dakua (Club Ambassador)", "Miss. Suraj Yadav (Club Ambassador)"]` |
