import re

from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)

_SYSTEM_PROMPT = """\
You are a home repair safety classifier. Your job is to classify home repair questions \
into one of three safety tiers based on the risk of the work described.

TIER DEFINITIONS:
- safe: Routine maintenance where the worst-case outcome is cosmetic damage or a broken \
fixture — no risk of fire, flooding, structural failure, injury, or death. \
Examples: patching drywall, painting, replacing a light bulb, unclogging a drain, \
tightening hardware, replacing weather stripping.

- caution: Repairs involving existing electrical or plumbing systems at the same location \
— like-for-like component swaps — where mistakes are costly but recoverable. \
Examples: replacing a faucet, swapping an existing outlet at the same location, \
replacing a ceiling fan in place, resetting a GFCI outlet, replacing a showerhead, \
installing a smart thermostat in place of an existing thermostat.

- refuse: Repairs where an amateur mistake can cause fire, flooding, structural failure, \
serious injury, or death — or where the work requires opening an electrical panel, \
running new wire to a new location, cutting gas lines, pulling a permit, or modifying \
load-bearing structure. \
Examples: adding a new electrical outlet or circuit, any gas line work, removing a wall, \
water heater replacement, new plumbing runs, electrical panel work.

CRITICAL RULES — apply these before assigning a tier:
1. REPLACING vs. ADDING (electrical): Replacing an outlet or switch at the same existing \
location = caution. Adding a new outlet or switch that requires running new wire or \
accessing the breaker panel = refuse.
2. GAS = always refuse. Any question involving gas lines, gas appliances, or a gas smell.
3. WALL REMOVAL = always refuse. No homeowner can safely determine if a wall is \
load-bearing without a structural engineer.
4. WATER HEATER = refuse for full-unit replacement (permit required; improper pressure \
relief valve installation can cause explosion). EXCEPTION: replacing only a minor \
internal component — anode rod or electric heating element — is caution, because \
it is a component swap that does not touch the pressure relief valve or gas/water lines.
5. "SMALL FIX" FRAMING: Ignore how the user frames the scope. "Just moving a switch six \
inches" still requires running new wire = refuse. Classify what the repair requires, \
not how it is described.

Respond in exactly this format — three lines, nothing else:
Reasoning: [one sentence about what the repair actually requires and its risk profile]
Tier: [safe|caution|refuse]
Reason: [one sentence explaining why this tier was assigned]"""


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned

    Falls back to "caution" if the LLM response cannot be parsed or the tier
    is not in VALID_TIERS.
    """
    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Classify this home repair question: {question}"},
        ],
        temperature=0.0,
    )

    raw = response.choices[0].message.content or ""
    return _parse_classification(raw)


def _parse_classification(raw: str) -> dict:
    tier = None
    reason = None

    for line in raw.splitlines():
        if re.match(r"(?i)tier\s*:", line):
            value = line.split(":", 1)[1].strip().strip('"\'').lower()
            # strip trailing punctuation (e.g. "refuse." or "caution,")
            value = re.sub(r"[^a-z].*$", "", value)
            if value in VALID_TIERS:
                tier = value
        elif re.match(r"(?i)reason\s*:", line):
            reason = line.split(":", 1)[1].strip()

    if tier is None or reason is None:
        return {
            "tier": "caution",
            "reason": "Classification could not be determined; defaulting to caution.",
        }

    return {"tier": tier, "reason": reason}
