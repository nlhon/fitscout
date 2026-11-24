# Grant Scout

Finds fashion grants whose deadlines haven't passed, then drafts applications for an
applicant (set up for Nova Lorraine) from a profile file. **It writes drafts only and never
submits anything.** Review each draft, fill the `[NEEDS INPUT]` gaps, and submit on the
grant's official site.

## How it works

1. **Search**: Claude (`claude-opus-5-5`) uses web search and web fetch to find fashion
   grants, fellowships and prizes and to read each one's official page.
2. **Extract**: the notes are turned into structured `Grant` records (deadline, award,
   eligibility, published application questions, required materials).
3. **Filter**: the code itself, not the model, drops any grant whose deadline is before
   today or can't be read. Rolling grants are kept unless you pass `--no-rolling`.
4. **Draft**: for each open grant, Claude answers the application questions in the
   applicant's voice using **only** facts from the profile, and marks anything missing.

## Budgets

Set `stage` in the profile (`concept`, `sampling`, `launch` or `growth`). Each draft's budget
starts from a stage-based split scaled to that grant's award, then is adapted to the grant's
rules. See [docs/budget_rationale.md](docs/budget_rationale.md) for the research behind it.

## Setup

```bash
cd agents/grant-scout
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # or `ant auth login`
cp profiles/nova_lorraine.example.yaml profiles/nova_lorraine.yaml
# fill in profiles/nova_lorraine.yaml (git-ignored)
```

## Usage

```bash
python -m grant_scout search --region "United States"         # -> output/open_grants.json
python -m grant_scout draft --profile profiles/nova_lorraine.yaml
python -m grant_scout run --profile profiles/nova_lorraine.yaml  # search + draft
python -m grant_scout draft --profile profiles/nova_lorraine.yaml --only "Fashion Fund"
```

Drafts go to `output/applications/<grant>.md`, each with an eligibility check, answers,
a "Still needed from you" checklist and the materials to attach.

Requests use server-side refusal fallbacks (`fallbacks: "default"`), so if the main
model declines a request, the API retries it on another model in the same call.

## Tests

```bash
python -m pytest tests
```
