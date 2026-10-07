---
name: code-inspection-root-cause
description: Inspect a reported code issue, trace its relevant execution path, and identify the root cause without modifying the codebase.
---
# Code Inspection & Root Cause Analysis

## Purpose

Perform read-only investigation of a reported code issue.

The goal is to identify:

- The failure point
- The relevant execution path
- The first incorrect input, decision, state, or transformation
- The responsible file, class, and function

Stop once the root cause is sufficiently supported by evidence.

## Mandatory Restrictions

- Read-only inspection only.
- Do not modify files.
- Do not generate implementation code.
- Do not run tests.
- Do not use terminal or shell commands.
- Do not install dependencies.
- Do not change configuration.
- Do not redesign the architecture.
- Do not inspect unrelated components.
- Do not assume the root cause.

## Inspection Process

### 1. Understand the Error

Identify:

- Exact error
- Actual input
- Expected input
- Operation that failed

### 2. Locate the Failure

Find:

- File
- Class
- Function/method
- Failing operation

Explain why the operation failed.

* [ ] 3. Trace the Relevant Input

Trace only the necessary path:

```text
User Input
↓
Entry Point
↓
Relevant Agent/Router
↓
Relevant Capability
↓
Relevant Tool/Function
↓
Failure
```
