from datetime import date

from grant_scout.drafter import render_markdown, slugify
from grant_scout.models import Answer, ApplicationDraft, Grant
from grant_scout.search import filter_open

TODAY = date(2026, 11, 24)


def g(name, deadline=None, rolling=False, org="Org"):
    return Grant(
        name=name, organization=org, url="https://example.org", deadline=deadline,
        deadline_is_rolling=rolling, award_amount=None, eligibility="", focus="",
        application_questions=[], required_materials=[],
    )


def test_drops_past_and_unknown_deadlines():
    grants = [g("Past", "2026-11-23"), g("Today", "2026-11-24"), g("Later", "2027-02-01"), g("Unknown")]
    assert [x.name for x in filter_open(grants, TODAY)] == ["Today", "Later"]


def test_rolling_included_last_and_optional():
    grants = [g("Rolling", rolling=True), g("Soon", "2026-12-01")]
    assert [x.name for x in filter_open(grants, TODAY)] == ["Soon", "Rolling"]
    assert [x.name for x in filter_open(grants, TODAY, include_rolling=False)] == ["Soon"]


def test_bad_date_and_duplicates():
    grants = [g("Bad", "next spring"), g("Dup", "2027-01-01"), g("dup ", "2027-01-05")]
    assert [x.name for x in filter_open(grants, TODAY)] == ["Dup"]


def test_render_markdown():
    draft = ApplicationDraft(
        grant_name="X", eligibility_assessment="Likely eligible.",
        answers=[Answer(question="Why?", answer="Because [NEEDS INPUT: reason].")],
        missing_information=["reason"], materials_checklist=["Portfolio"],
    )
    md = render_markdown(g("Fashion Fund", "2027-01-01"), draft, "Nova Lorraine")
    assert "Nova Lorraine" in md and "- [ ] reason" in md and "2027-01-01" in md
    assert slugify("CFDA / Fashion Fund 2027!") == "cfda-fashion-fund-2027"
