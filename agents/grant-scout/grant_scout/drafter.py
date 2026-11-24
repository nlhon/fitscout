"""Draft grant applications from an applicant profile.

Drafts are written to disk for the applicant to review and submit themselves.
Nothing here submits an application or contacts a grant-maker.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import anthropic
import yaml

from .models import ApplicationDraft, Grant
from .search import BETAS, MODEL, _check

SYSTEM = """You draft grant applications for a fashion designer, in their own first-person voice.

Rules:
- Use only facts present in the applicant profile. Never invent awards, press, revenue, \
stockists, collaborators, dates, numbers or biography.
- Where an answer needs a fact the profile lacks, write [NEEDS INPUT: what is needed] in \
the answer and list it under missing_information.
- Answer every published application question. If none are published, draft the usual \
sections: artist/designer statement, project description, how the funds will be used, \
budget outline, impact, and timeline.
- Respect any word or character limits stated in the question.
- Be specific and concrete, tie the work to the grant's stated focus, and avoid filler."""


def load_profile(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def draft_application(client: anthropic.Anthropic, grant: Grant, profile: Dict[str, Any]) -> ApplicationDraft:
    content = (
        "<applicant_profile>\n"
        + yaml.safe_dump(profile, sort_keys=False, allow_unicode=True)
        + "</applicant_profile>\n\n<grant>\n"
        + grant.model_dump_json(indent=2)
        + "\n</grant>\n\nDraft this application."
    )
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        betas=BETAS,
        fallbacks="default",
        output_config={"effort": "high"},
        system=SYSTEM,
        messages=[{"role": "user", "content": content}],
        output_format=ApplicationDraft,
    )
    _check(response)
    return response.parsed_output


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80] or "grant"


def render_markdown(grant: Grant, draft: ApplicationDraft, applicant: str) -> str:
    deadline = grant.deadline or ("Rolling" if grant.deadline_is_rolling else "Unknown")
    lines = [
        f"# {grant.name} — application draft for {applicant}",
        "",
        "> DRAFT. Review every answer, fill each [NEEDS INPUT] and confirm the details on the "
        "official page before submitting.",
        "",
        f"- **Organization:** {grant.organization}",
        f"- **Deadline:** {deadline}",
        f"- **Award:** {grant.award_amount or 'Not stated'}",
        f"- **Apply at:** {grant.url}",
        "",
        "## Eligibility check",
        "",
        draft.eligibility_assessment,
        "",
        "## Answers",
        "",
    ]
    for a in draft.answers:
        lines += [f"### {a.question}", "", a.answer, ""]
    if draft.missing_information:
        lines += ["## Still needed from you", ""] + [f"- [ ] {m}" for m in draft.missing_information] + [""]
    if draft.materials_checklist:
        lines += ["## Materials to attach", ""] + [f"- [ ] {m}" for m in draft.materials_checklist] + [""]
    return "\n".join(lines)


def write_draft(out_dir: Path, grant: Grant, draft: ApplicationDraft, applicant: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slugify(grant.name)}.md"
    path.write_text(render_markdown(grant, draft, applicant), encoding="utf-8")
    return path
