# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

---

### Tier definitions

**safe:**
```
Routine maintenance where the worst-case outcome if something goes wrong is cosmetic
damage or a broken fixture — no risk of fire, flooding, structural failure, injury,
or death (e.g., patching drywall, painting, replacing a light bulb, unclogging a drain).
```

**caution:**
```
Repairs involving existing electrical or plumbing systems at the same location —
like-for-like component swaps a motivated homeowner can complete — where mistakes are
costly but recoverable (e.g., replacing a faucet, swapping an outlet at the same
existing location, replacing a ceiling fan in place, installing a smart thermostat).
```

**refuse:**
```
Repairs where an amateur mistake can cause fire, flooding, structural failure, serious
injury, or death — or where the work requires running new wire, opening an electrical
panel, cutting into gas lines, pulling a permit, or modifying load-bearing structure
(e.g., adding a new electrical circuit, any gas work, removing walls, new plumbing runs).
```

---

### Classification approach

```
Chain-of-thought with precise tier definitions and explicit edge case rules.

The LLM reasons about what the repair actually requires in one sentence, then names the
tier. Asking for reasoning before the label forces evaluation of real-world risk rather
than keyword pattern-matching — this is especially important for boundary cases like
"replacing" vs. "adding" in electrical work, where the surface phrasing is similar but
the underlying task is completely different.

Few-shot examples were considered but skipped in favor of comprehensive explicit rules
for the two most common error cases (electrical replacing-vs-adding, and "small framing"
that minimizes refuse-tier work). Explicit rules scale better than examples when the
boundary is well-defined.
```

---

### Output format

```
The LLM returns three lines in this exact format:

Reasoning: [one sentence about what the repair actually requires and its risk profile]
Tier: [safe|caution|refuse]
Reason: [one sentence explaining why this tier was assigned]

Parsing logic:
- Search each line for "Tier:" and extract the value after the colon.
- Strip whitespace, strip surrounding quotes, lowercase.
- Validate against VALID_TIERS.
- Similarly extract "Reason:" for the reason field.
- If either parse fails or tier is not in VALID_TIERS, fall back to "caution".
```

---

### Prompt structure

**System message:**
```
You are a home repair safety classifier. Your job is to classify home repair questions
into one of three safety tiers based on the risk of the work described.

TIER DEFINITIONS:
- safe: Routine maintenance where the worst-case outcome is cosmetic damage or a broken
  fixture — no risk of fire, flooding, structural failure, injury, or death.
  Examples: patching drywall, painting, replacing a light bulb, unclogging a drain,
  tightening hardware, replacing weather stripping.

- caution: Repairs involving existing electrical or plumbing systems at the same location
  — like-for-like component swaps — where mistakes are costly but recoverable.
  Examples: replacing a faucet, swapping an existing outlet at the same location,
  replacing a ceiling fan in place, resetting a GFCI outlet, replacing a showerhead,
  installing a smart thermostat in place of an existing thermostat.

- refuse: Repairs where an amateur mistake can cause fire, flooding, structural failure,
  serious injury, or death — or where the work requires opening an electrical panel,
  running new wire to a new location, cutting gas lines, pulling a permit, or modifying
  load-bearing structure.
  Examples: adding a new electrical outlet or circuit, any gas line work, removing a wall,
  water heater replacement, new plumbing runs, electrical panel work.

CRITICAL RULES — apply these before assigning a tier:
1. REPLACING vs. ADDING (electrical): Replacing an outlet or switch at the same existing
   location = caution. Adding a new outlet or switch that requires running new wire or
   accessing the breaker panel = refuse.
2. GAS = always refuse. Any question involving gas lines, gas appliances, or a gas smell.
3. WALL REMOVAL = always refuse. No homeowner can safely determine if a wall is
   load-bearing without a structural engineer.
4. WATER HEATER = refuse. Permit required in most jurisdictions; improper pressure relief
   valve installation can cause explosion.
5. "SMALL FIX" FRAMING: Ignore how the user frames the scope. "Just moving a switch six
   inches" still requires running new wire = refuse. Classify what the repair requires,
   not how it is described.

Respond in exactly this format — three lines, nothing else:
Reasoning: [one sentence about what the repair actually requires and its risk profile]
Tier: [safe|caution|refuse]
Reason: [one sentence explaining why this tier was assigned]
```

**User message:**
```
Classify this home repair question: {question}
```

---

### Caution/refuse boundary

```
Rule: If completing this repair correctly requires opening an electrical panel, running
new wire to a new location, cutting into gas lines, pulling a permit, or modifying
load-bearing structure — OR if a mistake could cause fire, flooding, structural failure,
serious injury, or death — classify as refuse; otherwise classify as caution.

Example 1 (caution): "How do I replace an outlet that stopped working?"
The outlet is on an existing circuit at the same location — this is a component swap.
If wired incorrectly, the breaker trips. Worst case is a recoverable electrical fault,
not a fire hazard. → caution

Example 2 (refuse): "How do I add a new outlet to my garage?"
Adding means running a new circuit from the panel to a new location — panel access, new
wire run, permit required. An amateur mistake creates a concealed fire hazard. → refuse
```

---

### Fallback behavior

```
If the LLM response cannot be parsed (no "Tier:" line found, or the extracted value is
not in VALID_TIERS), return:
  {"tier": "caution", "reason": "Classification could not be determined; defaulting to
   caution out of an abundance of caution."}

Failing to "caution" rather than "safe" is the correct choice here: a "safe" fallback
would allow the responder to answer a potentially refuse-tier question with no guardrails.
A "caution" fallback keeps a safety warning in front of the user while still providing
some guidance. Failing to "refuse" was considered but would be too disruptive for a
simple parsing error on a genuinely safe question.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
"Can I replace a light switch that stopped working?" — I expected caution and it returned
caution correctly, but I initially worried the classifier might flag "electrical" work too
broadly as refuse. The critical rule about "replacing existing at same location" kept it
correctly in caution.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
Added the explicit CRITICAL RULES section after noticing the initial prompt (definitions
only) was inconsistently classifying "add a new outlet" — sometimes returning caution
because it pattern-matched on "outlet" rather than reasoning about "new circuit." The
explicit rule "ADDING a new outlet = refuse" eliminated the ambiguity.
```
