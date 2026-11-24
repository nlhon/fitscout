"""Command line entry point.

  python -m grant_scout search                 # list open fashion grants
  python -m grant_scout draft --profile P      # draft applications from saved grants
  python -m grant_scout run --profile P        # search, then draft
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

import anthropic

from .drafter import draft_application, load_profile, write_draft
from .models import Grant, GrantList
from .search import filter_open, find_open_grants

OUT = Path("output")
GRANTS_FILE = OUT / "open_grants.json"


def _print_grants(grants):
    if not grants:
        print("No open grants found.")
        return
    for g in grants:
        deadline = g.deadline or "Rolling"
        print(f"- {deadline:<10}  {g.name} ({g.organization})  {g.award_amount or ''}\n    {g.url}")


def cmd_search(args, client) -> list[Grant]:
    grants = find_open_grants(
        client, limit=args.limit, region=args.region, include_rolling=not args.no_rolling
    )
    OUT.mkdir(exist_ok=True)
    GRANTS_FILE.write_text(GrantList(grants=grants).model_dump_json(indent=2), encoding="utf-8")
    print(f"{len(grants)} open grants (saved to {GRANTS_FILE}):")
    _print_grants(grants)
    return grants


def cmd_draft(args, client, grants=None) -> None:
    if grants is None:
        if not GRANTS_FILE.exists():
            sys.exit(f"{GRANTS_FILE} not found; run `search` first.")
        grants = GrantList.model_validate_json(GRANTS_FILE.read_text(encoding="utf-8")).grants
        # Re-check deadlines in case the saved list is old.
        grants = filter_open(grants, date.today(), include_rolling=True)
    if args.only:
        grants = [g for g in grants if args.only.lower() in g.name.lower()]
    profile = load_profile(Path(args.profile))
    applicant = profile.get("name", "applicant")
    out_dir = OUT / "applications"
    for g in grants:
        print(f"Drafting: {g.name} ...", flush=True)
        try:
            draft = draft_application(client, g, profile)
        except (anthropic.APIError, RuntimeError) as e:
            print(f"  skipped: {e}")
            continue
        path = write_draft(out_dir, g, draft, applicant)
        print(f"  -> {path}  ({len(draft.missing_information)} items need your input)")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="grant_scout", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("search", "run"):
        s = sub.add_parser(name)
        s.add_argument("--limit", type=int, default=15, help="roughly how many grants to look for")
        s.add_argument("--region", help="prioritise grants open to this country/region, e.g. 'United States'")
        s.add_argument("--no-rolling", action="store_true", help="exclude rolling-deadline grants")
    for name in ("draft", "run"):
        s = sub.choices.get(name) or sub.add_parser(name)
        s.add_argument("--profile", required=True, help="applicant profile YAML")
        s.add_argument("--only", help="draft only grants whose name contains this text")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    client = anthropic.Anthropic()
    if args.cmd == "search":
        cmd_search(args, client)
    elif args.cmd == "draft":
        cmd_draft(args, client)
    else:
        cmd_draft(args, client, grants=cmd_search(args, client))


if __name__ == "__main__":
    main()
