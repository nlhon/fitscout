"""Find fashion grants on the web and keep only those still open."""

from __future__ import annotations

import logging
from datetime import date
from typing import List, Optional

import anthropic

from .models import Grant, GrantList

log = logging.getLogger(__name__)

MODEL = "claude-opus-5-5"
BETAS = ["server-side-fallback-2026-07-01"]
MAX_CONTINUATIONS = 5

RESEARCH_PROMPT = """Today is {today}. Find fashion grants, fellowships, artist residencies, incubators, prizes and funds \
that are currently accepting applications, i.e. whose next deadline is on or after {today}, \
or that accept applications on a rolling basis.

Cover fashion design, apparel, textiles, accessories, sustainable fashion, and grants for \
emerging or independent designers and small fashion businesses. Include artist fellowships \
and residencies that accept designers, textile artists or interdisciplinary/art-and-technology \
practitioners, even if they are not fashion-only.{extra}

For every grant, open its official page and record:
- name and organization
- official URL
- the exact next deadline (date), or that it is rolling
- award amount
- eligibility (location, citizenship, age limits, years in business, career stage, business size)
- what it funds
- the application questions or required sections, as published
- required materials (portfolio, budget, CV, etc.)

Only report a deadline you saw stated on an official or reliable page for the current cycle. \
If a page only shows a past cycle's deadline, say so instead of guessing the next one. \
Aim for {limit} grants."""

EXTRACT_PROMPT = """Convert the research notes below into a structured list of grants. \
Use only information in the notes; do not invent deadlines, amounts or questions. \
Write deadlines as YYYY-MM-DD. If a deadline is unknown or only a past cycle is known, \
set deadline to null and deadline_is_rolling to false.

<notes>
{notes}
</notes>"""


def _text(message) -> str:
    return "\n".join(b.text for b in message.content if b.type == "text")


def _check(message) -> None:
    if message.stop_reason == "refusal":
        details = message.stop_details
        raise RuntimeError(f"Request declined: {details.explanation if details else 'no details'}")


def research(client: anthropic.Anthropic, today: date, limit: int, region: Optional[str]) -> str:
    """Run a web research pass and return the notes as text."""
    extra = f"\nPrioritise grants open to applicants in {region}." if region else ""
    messages = [
        {"role": "user", "content": RESEARCH_PROMPT.format(today=today.isoformat(), extra=extra, limit=limit)}
    ]
    tools = [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": 20},
        {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 30},
    ]
    for _ in range(MAX_CONTINUATIONS + 1):
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=64000,
            betas=BETAS,
            fallbacks="default",
            output_config={"effort": "high"},
            tools=tools,
            messages=messages,
        ) as stream:
            message = stream.get_final_message()
        _check(message)
        if message.stop_reason != "pause_turn":
            return _text(message)
        # Server-side tool loop paused; resend so it resumes where it left off.
        messages = [messages[0], {"role": "assistant", "content": message.content}]
    log.warning("Research stopped after %d continuations", MAX_CONTINUATIONS)
    return _text(message)


def extract(client: anthropic.Anthropic, notes: str) -> List[Grant]:
    """Turn free-text research notes into validated Grant objects."""
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        betas=BETAS,
        fallbacks="default",
        messages=[{"role": "user", "content": EXTRACT_PROMPT.format(notes=notes)}],
        output_format=GrantList,
    )
    _check(response)
    return response.parsed_output.grants


def filter_open(grants: List[Grant], today: date, include_rolling: bool = True) -> List[Grant]:
    """Keep grants whose deadline is today or later (and rolling ones, optionally).

    Grants with no usable deadline are dropped, so nothing expired slips through.
    Results are sorted by soonest deadline, rolling grants last.
    """
    open_grants = []
    seen = set()
    for g in grants:
        key = (g.name.strip().lower(), g.organization.strip().lower())
        if key in seen:
            continue
        d = g.deadline_date()
        if (d is not None and d >= today) or (d is None and g.deadline_is_rolling and include_rolling):
            seen.add(key)
            open_grants.append(g)
    return sorted(open_grants, key=lambda g: (g.deadline_date() is None, g.deadline_date() or date.max))


def find_open_grants(
    client: anthropic.Anthropic,
    today: Optional[date] = None,
    limit: int = 15,
    region: Optional[str] = None,
    include_rolling: bool = True,
) -> List[Grant]:
    today = today or date.today()
    notes = research(client, today, limit, region)
    return filter_open(extract(client, notes), today, include_rolling)
