Got it. Here’s the full version of your pm/agents.md — clean, aligned with your wiki style, and practical for vibe-coding.
It’s short on ceremony, long on clarity. This file defines how agents should translate a short, exploratory prompt into a PM brief that you can quickly scan and align on before any build begins.

⸻


# Agent Protocol — Product Management Format

This file defines how agents write Product Management (PM) briefs.  
A PM brief is not a spec — it’s a structured **alignment artifact** used to clarify scope, purpose, and assumptions before code is written.

PM briefs capture intent.  
They exist to keep everyone (human or agent) in sync before work starts — reducing friction, wasted cycles, and misinterpretation.

---

## File Naming Convention

PM briefs live in the `pm/` directory.

**Format**

__.md

**Examples**
- `viewer__paste_parse.md`
- `agent__memory_editor.md`
- `forecast__error_insights.md`
- `core__session_restore.md`

**Guidelines**
- Use lowercase with double underscores `__` between parts.  
- Keep names short, memorable, and descriptive.  
- Each file represents a single coherent feature set (1 epic).  
- Archive outdated briefs with `_archive` if they’ve been replaced.  
- Avoid version numbers; update in place when possible.

---

## 1. Purpose

A PM brief exists to:
1. Clarify **why** a feature is needed.  
2. Define **what outcome** success looks like.  
3. Outline **what’s in and out of scope**.  
4. Structure the idea into **epic → features → stories**.  
5. Surface **alignment questions** before execution.

---

## 2. Standard Outline

Every PM file follows this structure:

```markdown
# Title

---

### Table of Contents
1. [Summary](#summary)
2. [Problem Statement](#problem-statement)
3. [Jobs To Be Done](#jobs-to-be-done)
4. [Feature Structure](#feature-structure)
5. [Out of Scope](#out-of-scope)
6. [Questions for Alignment](#questions-for-alignment)

---

## Summary
One short paragraph that states what the functionality enables and why it matters.
Avoid implementation detail.  
Think of it as a **north star** for what this feature contributes.

## Problem Statement
Describe the friction or opportunity driving this feature.  
Keep it human and temporal — what pain or inefficiency triggered this idea?

Example:
> Users have to manually create markdown files and structure content into cells.  
> This slows down capture and breaks creative flow.

## Jobs To Be Done
Define what users or agents are *actually* trying to achieve.  
Use JTBD phrasing when possible:

> When [situation], I want to [motivation], so I can [expected outcome].

Example:
> When I paste unstructured notes, I want them automatically parsed into readable sections so I can move from capture to comprehension instantly.

## Feature Structure
Outline the proposed structure at three levels: **Epic → Features → Stories.**

### Epic
A one-line summary of the overarching initiative.

### Features
List the core functional pillars.  
Each should be atomic — something that could exist independently but relates to the same goal.

### Stories
Break features into short, outcome-focused user stories.

Example:

**Epic:** Quick Text Import

**Features**
1. Text input dialog with parsing preview  
2. Markdown generation and file save  
3. Configurable parsing strategies  

**Stories**
- As a user, I can paste raw text and see a live preview of how it will parse.  
- As a user, I can select between parsing modes (paragraph, heading-aware, list).  
- As a user, I can save the parsed output as a markdown file and open it immediately.

## Out of Scope
List any ideas or functions that are **explicitly not** part of this iteration.  
This protects focus.

Example:
- AI-assisted parsing  
- Rich-text formatting  
- Collaboration tools  

You can include *future-state concepts* here if they help frame direction:
> Future versions may support AI-assisted structure detection and semantic grouping.

## Questions for Alignment
Open points or dependencies that must be clarified before build begins.

Examples:
- Should parsing strategies be configurable globally or per import?  
- What’s the default save directory for new files?  
- Does the file auto-open in viewer or require manual navigation?

---

## 3. Agent Behavior

When creating a PM brief:
1. Read the user’s short natural-language prompt (usually 1–5 sentences).  
2. Interpret **intent** and **scope** — don’t over-specify.  
3. Produce a markdown file following the above outline.  
4. Keep language concise, scannable, and free of filler.  
5. Avoid implementation details — only describe *what will exist*, not *how*.  
6. Include *Questions for Alignment* to invite feedback before building.

---

## 4. Example PM Brief

```markdown
# Viewer — Paste & Parse Text

---

### Table of Contents
1. [Summary](#summary)
2. [Problem Statement](#problem-statement)
3. [Jobs To Be Done](#jobs-to-be-done)
4. [Feature Structure](#feature-structure)
5. [Out of Scope](#out-of-scope)
6. [Questions for Alignment](#questions-for-alignment)

---

## Summary
Enable users to paste unstructured text and automatically transform it into structured markdown cells, preserving flow and readability.

## Problem Statement
Today, users manually create and format markdown documents before importing them.  
This adds unnecessary friction during idea capture and interrupts creative rhythm.

## Jobs To Be Done
> When I paste notes or copied content, I want them automatically structured into markdown cells so I can organize and annotate quickly.

## Feature Structure

**Epic:** Paste & Parse Text  
**Features**
1. Text input dialog with parsing preview  
2. Markdown generation with cell structure  
3. File save and auto-open in viewer  

**Stories**
- As a user, I can paste text into a dialog box.  
- As a user, I can preview parsed markdown before saving.  
- As a user, I can save the file and open it in the viewer immediately.

## Out of Scope
- AI-based semantic parsing  
- Custom markdown templates  
- Collaborative editing  

## Questions for Alignment
- Should parsing happen client-side or in the backend?  
- Do we allow configurable parsing modes?  
- Where do saved files live by default?


⸻

5. Closing Thought

PM briefs exist to create clarity before commitment.
Their job is alignment — not instruction.
A good brief invites discussion, sparks refinement, and ends in shared understanding.

---

This version stays short, keeps the **epic–feature–story** hierarchy explicit, and includes just enough product-thinking structure (JTBD, alignment questions) to match how you actually collaborate with agents before any build.