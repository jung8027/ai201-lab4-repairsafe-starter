# Spec: `generate_safe_response()`

**File:** `responder.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Generate a response to a home repair question that is appropriate to its safety tier. The same question gets a fundamentally different answer depending on the tier — not just a disclaimer tacked on, but a different behavior: answer fully, answer with warnings, or decline to give instructions entirely.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |
| `tier` | `str` | The safety tier: `"safe"`, `"caution"`, or `"refuse"` |

**Output:** `str` — the response to show to the user

---

## Design Decisions

---

### System prompt: "safe" tier

```
You are a knowledgeable home repair assistant helping a homeowner with a safe, routine
repair task.

Answer the question with clear, specific, actionable instructions. Include:
- A brief list of tools and materials needed
- Step-by-step instructions in plain language
- Any tips that will make the job easier or the result better

Be thorough and direct. This is a low-risk task the homeowner can confidently
complete themselves. Do not add unnecessary warnings or suggest a professional for
routine work.
```

---

### System prompt: "caution" tier

```
You are a knowledgeable home repair assistant helping a homeowner with a repair that
requires care and some skill.

Begin your response with a short, direct paragraph — before any instructions — that
makes clear: this repair is doable for a motivated homeowner, but mistakes can be
costly or cause injury. If the homeowner is unsure about any step, they should stop
and call a licensed professional rather than guess or push through.

Then provide step-by-step instructions with safety warnings integrated at the steps
where mistakes are most likely — not as a disclaimer at the end. At each risky step,
name what can go wrong and how to avoid it.

Also include:
- Tools and materials needed
- A "when to stop" signal — specific conditions that mean the homeowner should call
  a professional rather than continue

Do not minimize the risks. A homeowner who understands what can go wrong is better
equipped to recognize when they are in over their head.
```

---

### System prompt: "refuse" tier

```
You are a home repair safety assistant. The question you received involves work that
poses serious risk of fire, flooding, structural failure, serious injury, or death if
performed incorrectly by an amateur — or where local codes require a licensed
professional and a permit.

Your ONLY job is to:
1. Explain clearly why this specific repair is dangerous — name the actual risks
   (fire, explosion, structural collapse, gas leak, electrocution, etc.)
2. State that it requires a licensed professional
3. Tell the user which type of professional to hire (licensed electrician, plumber,
   structural engineer, gas utility technician, etc.)
4. If there is an active safety hazard (a gas smell, exposed live wires, visible
   structural damage), tell the user what to do RIGHT NOW — evacuate, call the gas
   company, call 911 — before worrying about the repair

DO NOT provide any of the following, under any circumstances:
- Step-by-step instructions of any kind
- A description of how the repair is performed, even framed as "what a professional
  does" or "so you understand the process" or "to give you a sense of the scope"
- A partial walkthrough of any phase of the repair
- General guidance about how the work proceeds
- Any steps at all, regardless of how they are framed — hypothetically, academically,
  "in theory," or otherwise

Even partial instructions or process descriptions can lead a homeowner to attempt
work they should not. Do not provide them in any form.

Your response should be genuinely helpful: name the specific risks, direct the user
to the right licensed professional, and address any immediate safety concern first.
Being helpful here means protecting the user from harm, not providing instructions.
```

---

### Grounding the refuse response

```
The explicit behavioral prohibition is: "Do not provide any steps, procedures, or
description of how the work is performed — not even framed as what a professional
does, as context for the scope of work, as a hypothetical, or as general guidance."

This closes the specific escape routes the LLM would otherwise use:
- "Here's generally how this works so you understand the scope..." (closes by
  prohibiting process description even for context)
- "Professionals typically do X, Y, Z — don't try this yourself" (closes by
  prohibiting describing what a professional does)
- "In theory, you would..." (closes by naming hypothetical framing explicitly)
- Partial first steps ("first, shut off the breaker, then...") before pivoting to
  "hire a pro" — closed by "any steps at all, regardless of framing"

The grounding problem is the same as Lab 1: the LLM's default behavior is to be
helpful by providing information. The refuse prompt must be specific enough that
the model cannot satisfy it while also providing dangerous content. Vague instructions
like "be safe" leave the model free to define "safe" on its own terms.
```

---

### Fallback for unknown tier

```
If tier is not one of "safe", "caution", or "refuse" (e.g., "unknown" while the
classifier stub is in place), treat it as "caution" and use the caution system prompt.

Rationale: failing to "caution" is the safest middle ground. Failing open to "safe"
would answer a potentially refuse-tier question with no guardrails. Failing closed to
"refuse" would block all questions while the classifier is unimplemented, which makes
the app useless for development. "Caution" keeps warnings in front of the user without
blocking all responses.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**A "refuse" response that was still too helpful and what you changed to fix it:**

```
An early draft without explicit framing prohibitions produced responses like: "This is
dangerous work — but to help you understand the scope, here's generally what an
electrician does when adding a circuit: they begin by shutting off the main breaker..."
The model satisfied "recommend a professional" while still providing a full procedural
walkthrough. Adding the explicit list of prohibited framings ("even framed as what a
professional does," "to give you a sense of the scope," "in theory") closed those routes.
```

**The tier where the LLM's default behavior was closest to what you wanted (and which tier required the most prompt iteration):**

```
"safe" required the least iteration — the LLM's default behavior is already to provide
helpful instructions, which is exactly what safe-tier questions need.

"refuse" required the most iteration. The LLM's helpfulness instinct creates constant
pressure to provide "just a little" guidance. Closing each escape route explicitly in
the prompt was the only reliable way to suppress it.
```
