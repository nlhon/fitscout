"""Stage-aware budget planning for grant applications.

Splits an award across the spending areas that are most viable, and most fundable,
at a brand's current stage. The rules come from the research in docs/budget_rationale.md:

- Reviewers score budget clarity on its own and reward named, quantified line items
  linked to a milestone (e.g. "first 30 units for the spring drop").
- The budget has to look reasonable against the award and the project's goals.
- New designers tend to budget for samples and forget grading, packaging and shipping,
  so every plan keeps an operations and contingency line.
- At an early stage, paying for sales is cheaper and less risky through commission
  (agents usually take 10-15%) or a market-week fee than through salaried staff, and
  many grants exclude payroll. A paid role is only suggested for large awards.

The planner gives a starting point. The drafter adapts it to each grant's rules, and
Nova checks every figure against real quotes before submitting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Category:
    key: str
    label: str
    share: float  # fraction of the award
    rationale: str
    example_items: str


STAGES = {
    "concept": [
        Category("development", "Design development & tech packs", 0.30,
                 "Turns ideas into specs a factory can quote and sample.",
                 "pattern making, tech packs, fit model sessions"),
        Category("sampling", "First samples (2-3 rounds)", 0.35,
                 "A physical sample is the proof most funders and buyers want first.",
                 "sample-room fees, toiles, revisions"),
        Category("materials", "Fabric & trim sourcing", 0.20,
                 "Swatches and minimums decide cost, quality and sustainability claims.",
                 "swatch cards, sample yardage, trims"),
        Category("ops", "Operations & contingency", 0.15,
                 "Covers shipping, fittings and the cost overruns sampling always has.",
                 "courier, fittings, 10% contingency"),
    ],
    "sampling": [
        Category("sampling", "Sampling & fit approval", 0.40,
                 "Getting to a production-ready sample is the gate to everything else.",
                 "2-3 sample rounds per style, grading"),
        Category("materials", "Production fabric commitments", 0.20,
                 "Locks in pricing and lead times for the first run.",
                 "fabric deposits, trims, labels"),
        Category("content", "Lookbook & product photography", 0.15,
                 "Needed to pre-sell and to pitch buyers and press.",
                 "photographer, model, studio day"),
        Category("presell", "Pre-order launch", 0.10,
                 "Validates demand before paying for inventory.",
                 "pre-order page, small paid-social test"),
        Category("ops", "Operations & contingency", 0.15,
                 "Shipping, packaging and overruns.",
                 "packaging, courier, 10% contingency"),
    ],
    "launch": [
        Category("production", "First production run", 0.35,
                 "Inventory is a revenue-generating asset that funders can see.",
                 "small-batch run of best-selling styles"),
        Category("marketing", "Launch marketing & PR", 0.25,
                 "Launch guides say this is where founders underspend.",
                 "paid social, influencer seeding, PR outreach"),
        Category("ecommerce", "E-commerce & content", 0.15,
                 "Converts launch attention into sales.",
                 "site upgrades, product photography"),
        Category("sampling", "Next-season samples", 0.10,
                 "Keeps the product pipeline moving.",
                 "1-2 sample rounds"),
        Category("ops", "Packaging, fulfilment & contingency", 0.15,
                 "Often forgotten and needed for every order.",
                 "branded packaging, shipping, 10% contingency"),
    ],
    "growth": [
        Category("production", "Capsule production of proven designs", 0.35,
                 "Turns runway and press attention into a sellable, revenue-generating range.",
                 "small-batch or made-to-order run of the strongest runway looks"),
        Category("sampling", "Next-collection development & sampling", 0.20,
                 "Shows funders the brand has a pipeline past its debut.",
                 "patterns, toiles, 2-3 sample rounds"),
        Category("wholesale", "Wholesale & sales development", 0.15,
                 "Opens repeat revenue. Commission-based sales and market-week fees "
                 "cost less up front than salaried staff.",
                 "showroom or market-week fee, line sheets, commission-based sales agent"),
        Category("marketing", "Marketing, content & PR", 0.15,
                 "Keeps the brand visible between shows and drives direct sales.",
                 "e-commerce photography, targeted paid social, press seeding"),
        Category("innovation", "Digital & innovation", 0.07,
                 "Funds the brand's distinctive tech-led side, which innovation grants reward.",
                 "AI design visualisation, digital product pages"),
        Category("ops", "Operations & contingency", 0.08,
                 "Shipping, packaging, insurance and overruns.",
                 "packaging, courier, insurance, contingency"),
    ],
}

SMALL_AWARD = 5_000
STAFF_AWARD = 50_000


@dataclass
class LineItem:
    label: str
    amount: int
    rationale: str
    example_items: str


def parse_amount(text: Optional[str]) -> Optional[int]:
    """Read the largest dollar figure in an award description, e.g. 'up to $25,000' -> 25000."""
    if not text:
        return None
    values = []
    for num, suffix in re.findall(r"\$?\s*(\d[\d,]*(?:\.\d+)?)\s*([kKmM])?", text):
        try:
            v = float(num.replace(",", ""))
        except ValueError:
            continue
        v *= {"k": 1_000, "m": 1_000_000}.get(suffix.lower(), 1)
        values.append(v)
    return int(max(values)) if values else None


def plan_budget(stage: str, amount: int) -> List[LineItem]:
    """Split an award across the areas that fit the brand's stage.

    Small awards are concentrated on the two highest-priority areas plus contingency,
    since one clear outcome reads better than many tiny lines. Large awards at the
    growth stage add a part-time sales/operations role.
    """
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; choose from {', '.join(STAGES)}")
    cats = list(STAGES[stage])
    if amount < SMALL_AWARD:
        ops = [c for c in cats if c.key == "ops"]
        top = sorted((c for c in cats if c.key != "ops"), key=lambda c: -c.share)[:2]
        cats = top + ops
    if stage == "growth" and amount >= STAFF_AWARD:
        cats = cats + [Category(
            "staff", "Part-time sales & operations coordinator", 0.15,
            "Only at this award size does a paid role pay back; check the grant allows payroll.",
            "part-time, fixed-term role tied to a wholesale target")]
    total = sum(c.share for c in cats)
    items = [LineItem(c.label, int(round(amount * c.share / total, -1)), c.rationale, c.example_items) for c in cats]
    items[-1].amount += amount - sum(i.amount for i in items)  # absorb rounding
    return items


def render_plan(items: List[LineItem]) -> str:
    return "\n".join(f"- {i.label}: ${i.amount:,} ({i.example_items}). {i.rationale}" for i in items)
