# News Evaluation Flow

This project compares two generated financial news articles (for example, one from Claude and one from Artham) against the original source content and produces a structured evaluation report.

The flow is designed so you can hand it over to developers as a private GitHub project they can later fork.

## What it Evaluates

For each article, the evaluator produces:

- Total score out of `100`
- Information retention score (vs source content)
- Readability score
- Presence of tables (`yes/no`)
- Presence of Chinese characters (`yes/no`)
- Presence of non-INR currency symbols (`yes/no`)
- Flags for potential `million/billion` to `lakh/crore` conversion inconsistencies

It also computes a comparison block showing which model performed better overall.

## Supported Input Context

The request schema includes configurable metadata that can be passed from upstream systems:

- `inflow.type`: `LODR` or `NEWS_STREAMER`
- `inflow.source_name`: for example `NSE LODR`, `Livsquawk`, `RSS`
- `publication_type`: `FIRST_PUBLISH` or `UPDATE`
- `source_content`: original filing/source text used as grounding

## Quick Start

1. Create and activate a Python virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy env file and add key:
   - `cp .env.example .env`
   - Set `OPENAI_API_KEY` in `.env`
4. Run:
   - `python -m src.main --input sample/input.json --output sample/output.json`

## Input Format

See `sample/input.json`.

Top-level fields:

- `request_id`
- `inflow`
- `publication_type`
- `source_content`
- `articles` with `claude` and `artham` article text
- Optional `weights` to tune scoring composition

## Output Format

See `sample/output.json` after running.

Key blocks:

- `scores.claude`
- `scores.artham`
- `comparison`
- `metadata_flags`

## Scoring Defaults

Default weight split:

- Information retention: `60`
- Readability: `40`

Total: `100`.

You can override these weights in input if needed.

## OpenAI Key

The evaluator uses OpenAI to assist with semantically grounded scoring:

- Information retention estimate from source vs article
- Readability estimate

Set:

- `OPENAI_API_KEY` in `.env`
- Optional: `OPENAI_MODEL` (default: `gpt-4.1-mini`)

If API call fails, the evaluator falls back to deterministic local heuristics so the pipeline can still run.

## Handing Over as Private GitHub Project

From this directory:

1. `git init`
2. `git add .`
3. `git commit -m "Initial news evaluation flow scaffold"`
4. Create a new **private** repo on your GitHub profile
5. Connect and push:
   - `git remote add origin <your-private-repo-url>`
   - `git branch -M main`
   - `git push -u origin main`

Then share access with developers, or ask them to fork if policy allows.
