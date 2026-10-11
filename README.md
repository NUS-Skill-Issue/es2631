# ES2631

**Critique and Communication of Thinking and Design**

A module skill in [NUS Skill Issue](https://github.com/NUS-Skill-Issue), part of **Skill Issue Labs**.

NUS Skill Issue is an organisation of module repositories. Each repository owns one module skill, its sources and its evaluations. The long term aim is to cover every NUS module. This repository is the ES2631 starter.

## What it does

- Explains the Elements of Thought and Intellectual Standards through the user's material.
- Helps with focused PEEL paragraphs and critiques of statements or slide decks.
- Reviews drafts for the strength of their reasoning and factual support.
- Extracts deck text and runs optional writing checks with local Python helpers.

The [official ES2631 course page](https://www.nus.edu.sg/celc/undergraduate-courses/es2631-critique-and-communication-of-thinking-and-design/) covers critique writing and a team academic oral presentation. This package currently concentrates on written critique. It is an experimental starter with no verified semester specific rubric.

## Try it

Give your assistant [SKILL.md](SKILL.md) and the reference folder, together with the question and relevant materials. In a host that already discovers the installed skill, invoke `$es2631`.

> Use the ES2631 skill to review this paragraph against my assignment brief. Identify the weakest inference and show one possible revision. Keep my position and stay within 180 words.

> Use the ES2631 skill to critique this deck using accuracy and fairness. Use only the deck and keep each paragraph below 150 words.

> Explain the difference between an Element of Thought and an Intellectual Standard using my design proposal.

The current brief determines word limits, assessment scope, required standards, citations and permitted AI use. This skill does not assume that every task needs nine paragraphs or a keyword quota.

## Repository layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Portable skill entry point |
| `references/` | Framework and task guidance |
| `scripts/` | Optional extraction and review helpers |
| `agents/openai.yaml` | Optional Codex display metadata |
| `module.json` | Module scope, source dates and known gaps |
| `evals/` | Behaviour checks and observed results |
| `tests/` | Helper regression tests |
| `docs/adding-a-module.md` | Conventions for the next independent module repository |

Automatic discovery and installation depend on the host. No global skill installation or hosted integration has been performed for this starter.

## Optional helpers

From this repository, with Python 3.10 or later available, run either helper with `--help`.

```sh
python3 scripts/check_essay.py --help
python3 scripts/extract_deck.py --help
```

The checker uses the Python standard library. PowerPoint extraction needs `python-pptx`. PDF extraction uses an available `pdfplumber`, `pypdf` or `pdftotext` installation. Dependencies are not installed automatically. Choose an output location appropriate for your own workspace.

For focused paragraphs, an explicit mapping is optional.

```sh
python3 scripts/check_essay.py paragraphs.txt --paragraphs-only --standards accuracy,fairness --limit 300
```

`--limit` is a hard maximum for the text being checked. `--require-all-elements` and `--style` enable optional observations. Use the first only when full element coverage is relevant. The checker cannot verify facts, determine authorship, certify rubric compliance or predict a grade. Extracted text does not replace inspecting charts and diagrams.

## Development status

See [evaluation results](evals/RESULTS.md). Written critique is the current scope. Dedicated presentation coaching, teamwork guidance and complete semester coverage remain open.

This is an independent student project, not an official NUS service. Redistribution licensing remains unresolved for the supplied starter components. See [provenance](PROVENANCE.md).
