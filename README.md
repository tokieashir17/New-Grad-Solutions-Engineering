# New Grad Solutions Engineering Jobs

An automatically updated job board for early-career:

- Solutions Engineering
- Sales Engineering
- Forward Deployed Engineering (FDE)
- Customer Engineering
- Solutions Consulting
- Technical / Implementation Engineering

The repository collects published jobs from supported ATS platforms, classifies them for early-career relevance, deduplicates postings, and regenerates this README.

## Current sources

- Greenhouse Job Board API
- Lever Postings API

The first version is intentionally API-first. Add companies to `data/companies.json`, then run the collector.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py
```

The generated dataset is written to `data/jobs.json`.

## Adding companies

Edit `data/companies.json`:

```json
[
  {
    "name": "Example",
    "ats": "greenhouse",
    "slug": "example"
  },
  {
    "name": "Example Lever",
    "ats": "lever",
    "slug": "examplelever"
  }
]
```

For Greenhouse, `slug` is the company's Greenhouse board token. For Lever, it is the company's Lever site name.

## GitHub Actions

The workflow in `.github/workflows/update.yml` runs every six hours and can also be started manually.

For a public repository, scheduled workflows can be delayed during high-load periods. GitHub recommends scheduling jobs at less busy times when possible.

## Classification

The classifier uses the title and description to identify:

1. Relevant role families
2. Early-career signals
3. Seniority exclusions
4. Geographic signals

It stores a relevance score and matched signals in `jobs.json`.

This is deliberately deterministic in V1. An LLM-based review/classification layer can be added later without changing the collector architecture.

## Roadmap

- [ ] Add Ashby
- [ ] Add more company sources
- [ ] Improve location normalization
- [ ] Add SQLite history
- [ ] Add "new today" and "new this week" sections
- [ ] Add GitHub Pages search/filter UI
- [ ] Add email/Discord notifications
- [ ] Add optional LLM classification
- [ ] Add source health checks

## Disclaimer

This project links to publicly published job postings. Always verify the opening and requirements on the employer's application page before applying.
