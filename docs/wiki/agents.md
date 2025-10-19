Got it — here’s the same file with just a clean, minimal addition for file-naming guidance.
It keeps the rhythm and tone intact while adding a small new section near the top.

⸻


# Agent Protocol — Wiki Narrative Format (Cognitive Edition)

This file defines how wiki narratives are written when describing systems, codebases, or computational concepts.  
The goal is to create **mental geometry** — helping humans and agents build *polymorphic intuition* rather than rote knowledge.

The wiki is where code becomes landscape.

---

## File Naming Convention

Wiki files live inside the `wiki/` directory.  
Each file name should clearly express its focus and stay short, mnemonic, and searchable.

**Format**

__.md

**Examples**
- `parser__architecture.md`
- `viewer__stateflow.md`
- `agent__memory.md`
- `core__philosophy.md`

**Guidelines**
- Use lowercase with double underscores `__` between parts.  
- Keep names descriptive but minimal (no version numbers or timestamps).  
- Each file represents a single conceptual landscape — not a log or changelog.  
- If a narrative is replaced or re-imagined, archive the old one and reuse the same name.

---

## 1. Philosophy

Code tells machines what to do.  
The wiki tells humans *how the code feels* — what ideas it embodies, how it moves, and where it fits in space.  

Each document should:
- Explain **conceptual topology** (how ideas connect).  
- Describe **motion** (how data, control, or meaning flows).  
- Anchor **spatial memory** (objects as places, functions as paths).  
- Maintain a **narrative rhythm** that supports long-term retention.

---

## 2. Standard Outline

Every wiki file begins with a title, a table of contents, and then these sections:

```markdown
# Title

---

### Table of Contents
1. [Summary](#summary)
2. [Cognitive Map](#cognitive-map)
3. [Narrative](#narrative)
4. [Reflections](#reflections)
5. [Artifacts](#artifacts)
6. [Appendix](#appendix)

---

## Summary
Explain what this part of the system is, and what role it plays.  
Keep it short — think of it as the *elevator pitch of comprehension*.

## Cognitive Map
This section gives the reader a mental model of the codebase —  
the **objects, functions, and relationships** that matter most.

Structure it like a narrated diagram:

### Objects
- `Viewer`: renders markdown nodes as composable cognition blocks.  
- `Parser`: transforms raw input into a structured intermediate form.  
- `Node`: smallest meaningful content unit — text, widget, or context marker.  

### Key Functions
- `parse_input(text)` → returns `Node[]`  
- `render_node(node)` → returns visual block  
- `attach_context(event)` → modifies node based on user state  

### Flow
Explain how these parts interact in plain language:
> “Input flows from the parser to the renderer.  
>  Context listeners act like tendons — adjusting each node as the user moves.”

### Spatial Analogy (Optional)
Map code onto metaphorical terrain.  
> “The parser is a river delta; text flows in as water, nodes branch like estuaries, and rendering collects into the ocean of the viewer.”

Use this section to make the code *memorable, mappable, and alive* in the listener’s head.

## Narrative
Tell the story of how this code evolved or why it exists.  
Use the rhythm: **Situation → Tension → Decision → Shift → Horizon.**

Avoid deep syntax here — focus on purpose and change over time.  
Make it temporal, not technical.

## Reflections
Distill 2–4 insights about design philosophy, constraints, or patterns that emerged.  
Example:
- “Functions mirror cognitive verbs — every method should describe an action, not a noun.”  
- “When in doubt, follow data flow, not inheritance.”

## Artifacts
Include light diagrams or pseudo-visuals only when they reinforce the mental map.

```mermaid
flowchart LR
A[Parser] --> B[Node Builder]
B --> C[Renderer]
C --> D[Viewer State]

---

That’s the minimal change you need — it now instructs exactly how to name and scope each wiki file without adding any clutter or new theory.