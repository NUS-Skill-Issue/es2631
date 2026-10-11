# Working from a deck

Extract the deck to locate evidence, then inspect the visual content needed for the critique. Slides can omit the spoken explanation. Do not fill those gaps with invented facts.

## Extraction

The optional helper accepts PowerPoint and PDF files.

```sh
python3 scripts/extract_deck.py deck.pptx --out deck.md
```

Run it from the skill folder or use full paths. Choose a scratch location allowed by the host for extracted text. Inspect `--help` for dependency and output options. Without a shell, use the host's document reader and preserve slide or page references manually.

Read speaker notes when available. Extraction can omit diagrams, screenshots, complex chart properties and spatial relationships. Inspect any visual supporting a claim even if that slide has plenty of extractable text. A low text warning is not a complete list of slides requiring visual review.

Never estimate an exact chart value from an unreadable image. Describe only an evident qualitative pattern or report the missing value. Keep page and slide numbering distinct where the export differs from the original.

## Evidence ledger

For each claim used, retain the slide number, the source wording or value, whether it comes from a chart or notes, and whether your interpretation goes beyond the source. Add an Element of Thought only where it helps the analysis.

| Deck content | Supported wording | Unsupported addition |
|---|---|---|
| “Cost reduced 30%”, with no baseline | The deck reports a 30% cost reduction but leaves the baseline unstated. | The design costs 30% less than the industry standard. |
| “Users preferred B” | The deck states that users preferred B. | Most users in the team's experiment strongly preferred B. |
| “Risk of supplier delay” | Supplier delay is identified as a risk. | Supplier delays caused the overrun. |
| No maintenance cost shown | The deck does not report a maintenance cost. | The team did not consider maintenance. |

## From evidence to critique

Locate the central recommendation, its purpose, evidence and assumptions. Evaluate the strongest relevant connections using the requested standards. Distinguish an omission in the communication from a demonstrated fault in the design or process.

A lecture deck might explain concepts without arguing for a design recommendation. Follow the user's question instead of forcing it into a project critique.

Respect a deck only source constraint. External evidence may test a claim when the brief allows it, but it cannot establish what the presenters knew or did. Keep additions separately attributed.

## Delivery

Write the requested critique or feedback. Add compact source locations for the important claims and identify any unreadable visuals or unresolved discrepancies. Provide the full ledger only when it would help the user check the result.
