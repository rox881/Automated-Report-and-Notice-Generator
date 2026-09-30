# UI Design: ChatGPT-Style Document Generator

Minimalist, distraction-free layout modeled after ChatGPT.

---

## Layout

```
┌──────────────────┬──────────────────────────────────────────────┐
│  SIDEBAR         │  MAIN WORKSPACE                              │
│                  │                                              │
│  [+ New Session] │                 Document Generator           │
│                  │                                              │
│  Recent History: │       ┌────────────────────────────────────┐ │
│  • Notice - Corp │       │ Paste source context here...       │ │
│  • Annual Report │       │                                    │ │
│  • Notice - Q3   │       └────────────────────────────────────┘ │
│                  │                                              │
│                  │       [ 📄 Notice Template ]  [ 📊 Report ]  │
│                  │                                              │
│  [User / Clear]  │       (Validation / Preview renders below)   │
└──────────────────┴──────────────────────────────────────────────┘
```

---

## Core Elements

### 1. Left Sidebar (Collapsible, Dark)
- **Top:** `+ New Session` button (clears context).
- **List:** Recent history (click to reload previous session/download).
- **Bottom:** Minimal actions (Clear history / Theme).

### 2. Center Stage (Main Area)
- **Context Box:** Centered auto-expanding input box for pasting raw context.
- **Template Selector (Pills/Buttons):**
  - `Notice Template`
  - `Report Template`
- **Inline Flow (Appears below input upon selection):**
  - **Check / Missing Fields:** Prompts only for missing values if needed.
  - **Preview & Edit:** Clean inline list/table of extracted values to verify.
  - **Generate & Download:** One-click `.docx` download button with status.

---

## Visual Style
- **Aesthetic:** Minimalist, neutral grays, rounded corners, soft shadows.
- **Focus:** No cluttered dashboards; interaction feels like a clean conversation stream.
