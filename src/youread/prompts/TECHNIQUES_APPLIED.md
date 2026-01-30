# Prompt Engineering Techniques Analysis
## OpenAI Prompting Guide → Video-to-Article Project

This document maps the techniques from OpenAI's GPT-5 prompting guide to our video-to-article project, explaining which techniques apply, how to use them, and which don't apply.

---

## Techniques Applied to Our Project

### 1. Structured XML Tags for Instructions
**Source:** Cursor's finding that `<[instruction]_spec>` tags improved instruction adherence

**Application:**
```xml
<role>...</role>
<core_principles>...</core_principles>
<output_contract>...</output_contract>
<code_handling>...</code_handling>
```

**Why it helps:** 
- LLM can internally reference specific sections
- Clear visual hierarchy in the prompt
- Easier to maintain and update individual sections

---

### 2. Avoiding Contradictory Instructions
**Source:** "Poorly-constructed prompts containing contradictory or vague instructions can be more damaging..."

**Application:**
Before:
```
❌ Be comprehensive AND Keep it concise
```

After:
```
✅ Be comprehensive: include all substantive points
✅ Be efficient: omit filler words and repetition
✅ There is no word limit
```

**Why it helps:**
- LLM doesn't waste reasoning tokens reconciling conflicts
- Clear priority when decisions must be made

---

### 3. Self-Reflection / Quality Rubrics
**Source:** "Asking the model to iteratively execute against self-constructed excellence rubrics"

**Application:**
```xml
<quality_check>
Before outputting, internally verify:
□ Did I capture the OPENING CONTEXT?
□ Did I include ALL MAIN ARGUMENTS?
□ Did I preserve the speaker's OPINIONS?
□ Would a reader understand EVERYTHING without watching?

If any answer is "no," revise before outputting.
</quality_check>
```

**Why it helps:**
- Forces self-evaluation before finalizing
- Catches common failure modes
- Improves consistency across different videos

---

### 4. Explicit Output Contract
**Source:** "Define the output contract: exact deliverables..."

**Application:**
```xml
<output_contract>
Your output MUST contain:
1. Title
2. Metadata line (format: **Speaker:** X | **Channel:** Y | **~Z min read**)
3. Introduction (1-2 paragraphs)
4. Body sections (## for major, ### for sub)
5. Code blocks with language tags
6. Key Takeaways (3-5 bullets)

Your output MUST NOT contain:
- Bullet points in main body
- References to "the video" or "watching"
- Timestamps
</output_contract>
```

**Why it helps:**
- No ambiguity about expected format
- Easy to validate output compliance
- Consistent structure across all outputs

---

### 5. Ambiguity Resolution Rules
**Source:** "Resolve ambiguity proactively: choose the most probable interpretation"

**Application:**
```xml
<ambiguity_resolution>
| Situation | Resolution |
|-----------|------------|
| Visual reference without description | Add: [Visual reference in video: ...] |
| Code syntax unclear | Use most idiomatic approach |
| Speaker contradicts themselves | Include both, note nuance |
| Technical term seems wrong | Use as spoken, don't correct |
</ambiguity_resolution>
```

**Why it helps:**
- Prevents the model from getting stuck
- Ensures consistent handling of edge cases
- Makes behavior predictable

---

### 6. Verbosity Guidance by Context
**Source:** Cursor's finding about "low verbosity globally, high verbosity for coding tools"

**Application:**
```xml
<verbosity_guidance>
HIGH VERBOSITY: Technical explanations, code, opinions, opening context
MEDIUM VERBOSITY: Anecdotes, comparisons, historical context
LOW VERBOSITY: Repeated points, filler phrases, meta-commentary
</verbosity_guidance>
```

**Why it helps:**
- Not all content deserves equal space
- Prevents bloat while maintaining completeness
- Matches reader expectations for different content types

---

### 7. Structured Few-Shot Examples
**Source:** Implicit throughout guide—all example prompts show clear input→output patterns

**Application:**
```xml
<example name="code_reconstruction">
<transcript_excerpt>
"Create a function called fetchData..."
</transcript_excerpt>
<correct_output>
```typescript
async function fetchData(userId: string): Promise<User> {
  // ...
}
```
</correct_output>
<why_correct_is_better>
- Provides actual runnable code
- Reader learns without watching
</why_correct_is_better>
</example>
```

**Why it helps:**
- Demonstrates exact expected behavior
- Covers tricky edge cases
- More effective than verbose instructions

---

### 8. Persistence/Completeness Mandate
**Source:** "Keep going until the user's query is completely resolved"

**Application:**
```xml
<completeness_mandate>
Your task is NOT complete until a reader could skip watching entirely.
- A 30-minute video typically produces 3,000-5,000 words
- If your output feels like a summary, it's too short
- There is NO WORD LIMIT
</completeness_mandate>
```

**Why it helps:**
- Overrides the model's tendency to be concise
- Establishes clear success criteria
- Prevents premature completion

---

### 9. Metaprompting for Iteration
**Source:** "Using GPT-5 as a meta-prompter for itself"

**Application:**
When output fails, use this template:
```
I have this prompt: [PROMPT]

Desired behavior: [WHAT YOU WANT]
Actual behavior: [WHAT HAPPENED]

What minimal edits would fix this?
```

**Why it helps:**
- Systematic approach to prompt debugging
- Leverages the LLM's own understanding of prompting
- Keeps changes minimal and targeted

---

## Techniques NOT Applicable (and Why)

| Technique | Why Not Applicable |
|-----------|-------------------|
| **Tool preambles** | Our task is single-shot generation, not multi-turn tool use |
| **Agentic eagerness control** | No autonomous decision-making needed |
| **Reasoning effort parameter** | OpenAI-specific; Claude has no equivalent |
| **Responses API** | OpenAI-specific infrastructure |
| **apply_patch format** | For code editing agents, not content generation |
| **Context gathering limits** | We provide complete context upfront (transcript) |
| **Tool call budgets** | No tools involved in generation |

---

## Key Insights from the Guide

### 1. Precision Matters More with Better Models
> "Its careful instruction-following behavior means that poorly-constructed prompts containing contradictory or vague instructions can be more damaging"

Modern models follow instructions closely—which means bad instructions cause bad outputs more reliably.

### 2. Structure Improves Adherence
Cursor found that XML tags like `<context_understanding>` significantly improved instruction following. We apply this throughout our prompt.

### 3. Different Verbosity for Different Contexts
Rather than one global verbosity setting, specify verbosity per content type. Critical for our use case where technical explanations need detail but transitions don't.

### 4. Self-Evaluation Improves Quality
Asking the model to check its work against criteria before finalizing catches errors that slip through otherwise.

### 5. Examples > Instructions
A well-chosen example demonstrating correct behavior is often more effective than paragraphs of explanation.

---

## Prompt Files Summary

After applying these techniques, our prompt system consists of:

| File | Purpose | Key Techniques Used |
|------|---------|---------------------|
| `system_prompt_v2.md` | Core instructions | XML tags, output contract, ambiguity resolution, quality check, completeness mandate |
| `examples_v2.md` | Few-shot examples | Structured examples with correct/incorrect comparison and explanation |

These files should be loaded and combined when calling the Claude API.

---

## Iteration Process

1. **Test** the prompt on 5 diverse videos
2. **Grade** each output (A/B/C)
3. **Diagnose** failures (which section of the prompt failed?)
4. **Use metaprompting** to identify fixes
5. **Apply minimal changes** to the relevant section
6. **Re-test** the same videos
7. **Repeat** until A-grade rate exceeds 80%

Track changes in version control. Document what worked and what didn't.
