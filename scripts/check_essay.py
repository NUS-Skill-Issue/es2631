#!/usr/bin/env python3
"""Report mechanical observations about an essay, not its quality or authorship.

Usage:
    python check_essay.py essay.txt \
        --standards clarity,accuracy,precision,relevance,depth,breadth,logic,significance,fairness \
        [--limit 1800] [--deck deck.md]

Paragraphs are separated by blank lines. Only when --standards is supplied, the
first and last paragraphs are treated as introduction and conclusion, and body
paragraph N is mapped to the Nth standard. Use --paragraphs-only to map every
paragraph instead. Markdown headings and anything from a
"References"/"Bibliography" line onward are ignored.

--deck compares numeric tokens with supplied text. A matching number does not
verify a claim, quotation, attribution, unit or context. The claims scan uses
selected patterns and is not exhaustive. --style enables optional style
observations, which cannot determine whether a human or AI wrote the text.

This is a prompt for judgement, not a grade. Fix real problems; don't game it.
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYWORDS = HERE.parent / "references" / "keywords.json"

REPLACE_ON_SIGHT = [
    "delve", "tapestry", "realm", "paradigm", "testament", "beacon", "multifaceted",
    "intricate", "holistic", "seamless", "seamlessly", "cutting-edge", "game-changer",
    "synergy", "unlock", "unleash", "embark", "underscore", "underscores", "showcase",
    "showcases", "pivotal", "crucial", "vital", "meticulous", "meticulously", "nuanced",
    "ever-evolving", "fast-paced", "landscape", "leverage", "leverages", "leveraging",
    "navigate", "navigating", "robust",
]
CLUSTER_WORDS = [
    "foster", "fosters", "harness", "harnessing", "elevate", "empower", "streamline",
    "transformative", "cornerstone", "comprehensive", "innovative", "dynamic", "notably",
    "ultimately", "utilize", "utilise", "facilitate", "facilitates",
]
BAD_OPENERS = ["moreover", "furthermore", "additionally", "in addition", "firstly", "secondly",
               "thirdly", "lastly", "in conclusion", "in today's", "in an era", "since the dawn"]
PATTERNS = {
    "negation mirror ('not X, it's Y' / 'not just X but Y')":
        r"\b(it'?s|this is|is) not (just |merely |only )?[^.;]{1,60}[,;—-]+\s*(it'?s|but|rather)\b|\bnot just\b[^.]{1,60}\bbut\b",
    "hedge stacking": r"\b(could|may|might) (potentially|possibly|perhaps|arguably)\b",
    "vague attribution": r"\b(experts|scientists|researchers|many people|critics) (agree|say|believe|argue|suggest)\b|\b(studies|research) (show|shows|suggest|suggests|has shown)\b|\bit is widely (believed|known|accepted)\b",
    "significance inflation": r"\b(plays? a (key|crucial|vital|pivotal|significant) role|a testament to|stands as|serves as a)\b",
    "empty closer": r"\b(only time will tell|the future looks bright|highlights the importance of|paves the way)\b",
    "chatbot residue": r"\b(I hope this|great question|certainly!|as an ai|let'?s dive|let'?s explore)\b",
    "performed candour": r"\b(let'?s be honest|here'?s the thing|real talk|to be fair,)\b",
}
PLACEHOLDER = r"\[[^\]]*(needed|not in deck|not stated|source|figure|verify|TBC|TODO)[^\]]*\]"


def load_bank():
    data = json.loads(KEYWORDS.read_text(encoding="utf-8"))
    return data["standards"], data.get("elements", {})


def elements_named(text, elements):
    return [name for name, pat in elements.items() if re.search(pat, text, re.I)]


def split_paragraphs(text):
    lines = text.replace("\r\n", "\n").split("\n")
    kept = []
    for ln in lines:
        s = ln.strip()
        if re.match(r"^(#+\s*)?(references|reference list|bibliography|works cited|sources)\s*:?\s*$", s, re.I):
            break
        if s.startswith("#"):
            kept.append("")
            continue
        kept.append(ln)
    paras = [re.sub(r"\s+", " ", p).strip()
             for p in re.split(r"\n\s*\n", "\n".join(kept))]
    return [p for p in paras if p]


def sentences(p):
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])", p) if s.strip()]


def words(t):
    return re.findall(r"[^\W_]+(?:['’-][^\W_]+)*", t, re.UNICODE)


def match_group(text, group):
    hits = []
    for e in group:
        if re.search(e["pattern"], text, re.I):
            hits.append(e["label"])
    return hits


def check_paragraph(i, p, std, bank, elements):
    out = []
    b = bank[std]
    name = match_group(p, b["name"])
    anchors = match_group(p, b["anchors"])
    support = match_group(p, b["supporting"])
    total = len(set(anchors) | set(support))
    wc = len(words(p))
    sc = len(sentences(p))
    out.append(f"[OBSERVE] Mapped paragraph {i} — {std.upper()}  ({wc} words, approximately {sc} sentences)")
    out.append(f"       standard wording matched: {', '.join(name) or 'none'}")
    out.append(f"       anchor patterns ({len(anchors)}): {', '.join(anchors) or 'none'}")
    out.append(f"       supporting patterns: {', '.join(support) or 'none'}; total labels {total}")
    els = elements_named(p, elements)
    out.append(f"       element wording matched: {', '.join(els) or 'none'}")
    return out, els


def pattern_scan(paras):
    out = []
    full = "\n\n".join(paras)
    low = full.lower()
    hits = sorted({w for w in REPLACE_ON_SIGHT if re.search(rf"\b{re.escape(w)}\b", low)})
    if hits:
        out.append(f"[STYLE] Words to review in context: {', '.join(hits)}")
    for n, p in enumerate(paras, 1):
        c = [w for w in CLUSTER_WORDS if re.search(rf"\b{w}\b", p.lower())]
        if len(c) >= 2:
            out.append(f"[WARN] Paragraph {n}: cluster words together: {', '.join(c)}")
    for n, p in enumerate(paras, 1):
        first = p.lower()
        for o in BAD_OPENERS:
            if first.startswith(o):
                out.append(f"[WARN] Paragraph {n} opens with '{o}'")
        for s in sentences(p)[1:]:
            if re.match(r"(moreover|furthermore|additionally)\b", s.lower()):
                out.append(f"[WARN] Paragraph {n}: sentence opens with '{s.split()[0]}'")
    openers = [words(p)[0].lower() for p in paras if words(p)]
    for n in range(1, len(openers)):
        if openers[n] == openers[n - 1]:
            out.append(f"[WARN] Paragraphs {n} and {n+1} both open with '{openers[n]}'")
    for label, pat in PATTERNS.items():
        found = re.findall(pat, full, re.I)
        if found:
            m = re.search(pat, full, re.I)
            out.append(f"[WARN] {label}: {len(found)}× e.g. “…{full[max(0,m.start()-20):m.end()+20].strip()}…”")
    wc = len(words(full))
    dashes = full.count("—") + len(re.findall(r"\s--?\s", full))
    if wc and dashes / wc * 500 > 1.0:
        out.append(f"[WARN] Dashes: {dashes} in {wc} words (aim ≤ ~1 per 500)")
    bolds = len(re.findall(r"\*\*[^*]+\*\*", full))
    if bolds:
        out.append(f"[WARN] {bolds} bold span(s) in essay text")
    lens = [len(words(s)) for p in paras for s in sentences(p)]
    if len(lens) > 5:
        sd = statistics.pstdev(lens)
        out.append(f"[INFO] Sentence length: mean {statistics.mean(lens):.1f}, spread (sd) {sd:.1f}"
                   + ("  ← low variety, rhythm may feel flat" if sd < 5 else ""))
    plens = [len(words(p)) for p in paras[1:-1]]
    if len(plens) > 3:
        sd = statistics.pstdev(plens)
        if sd < 12:
            out.append(f"[WARN] Body paragraph lengths very uniform (sd {sd:.0f} words); vary them")
    if not out or all(x.startswith("[INFO]") for x in out):
        out.insert(0, "[INFO] No selected style patterns found. This does not establish authorship.")
    return out


def numeric_tokens(text):
    text = text.replace("−", "-")
    return {n.replace(",", "") for n in re.findall(
        r"(?<![\w.])[+-]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?", text)}


def source_content(text):
    """Remove known generated labels from this helper's Markdown output."""
    if not text.startswith("# Deck extract:"):
        return text
    kept = []
    for line in text.splitlines():
        if line == "## Slides to inspect as images":
            break
        if (line.startswith("# Deck extract:")
                or re.match(r"^\d+ slides\.", line)
                or re.match(r"^\[table \d+\]$", line)
                or re.match(r"^\[\d+ image\(s\) on this slide\]$", line)
                or line.startswith("[extraction warning]")
                or (line.startswith("[chart]") and "WARNING" in line)):
            continue
        line = re.sub(r"^## Slide \d+:\s*", "", line)
        kept.append(re.sub(r"^\[chart\] plot \d+\s*", "", line))
    return "\n".join(kept)


def claims(paras, deck_text):
    out = ["[INFO] Selected claim patterns only. Numeric token presence does not verify claims, quotes, units or context."]
    ph = re.findall(PLACEHOLDER, "\n".join(paras), re.I)
    if ph:
        out.append(f"[TODO] {len(ph)} placeholder(s) to resolve or list in delivery notes:")
        out.extend("       " + p for p in ph)
    deck_nums = set()
    if deck_text:
        deck_nums = numeric_tokens(source_content(deck_text))
    flagged = []
    for n, p in enumerate(paras, 1):
        for s in sentences(p):
            has_num = re.search(r"\d", s)
            has_quote = re.search(r"[\"“][^\"”]{8,}[\"”]|(?<!\w)['‘][^'’]{8,}['’](?!\w)", s)
            has_attr = re.search(r"\baccording to\b|\breport(s|ed)\b|\bfound that\b|\bstudy\b|\bsurvey\b|\b(claims?|states?|argues?|suggests?)\b", s, re.I)
            if has_num or has_quote or has_attr:
                missing = []
                if deck_text and has_num:
                    missing = sorted(numeric_tokens(s) - deck_nums)
                flagged.append((n, s, missing))
    if flagged:
        out.append(f"[REVIEW] {len(flagged)} sentence(s) matched selected figure, quote or attribution patterns; check their sources:")
        for n, s, missing in flagged:
            tag = f"  ← numeric tokens not found in source text: {', '.join(missing)}" if missing else ""
            out.append(f"       P{n}: {s}{tag}")
    else:
        out.append("[INFO] No selected claim patterns found. Other claims may still require evidence.")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("essay")
    ap.add_argument("--standards", help="optional comma-separated standards mapped to body paragraphs in order")
    ap.add_argument("--limit", type=int, help="hard maximum word count using this tool's approximate counter")
    ap.add_argument("--deck", help="deck Markdown from extract_deck.py (or a supplied source text), for number cross-checking")
    ap.add_argument("--paragraphs-only", action="store_true",
                    help="map every block as a body paragraph (no intro/conclusion)")
    ap.add_argument("--require-all-elements", action="store_true",
                    help="explicitly require a wording match for every element; this does not verify substantive coverage")
    ap.add_argument("--style", action="store_true", help="show optional style observations, not authorship detection")
    args = ap.parse_args()
    if args.limit is not None and args.limit <= 0:
        ap.error("--limit must be a positive integer")

    try:
        bank, elements = load_bank()
        paras = split_paragraphs(Path(args.essay).read_text(encoding="utf-8"))
        deck_text = Path(args.deck).read_text(encoding="utf-8") if args.deck else ""
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        ap.error(str(exc))
    stds = [s.strip().lower() for s in (args.standards or "").split(",") if s.strip()]
    if args.standards is not None and not stds:
        ap.error("--standards must contain at least one standard")
    unknown = [s for s in stds if s not in bank]
    if unknown:
        sys.exit(f"Unknown standard(s): {', '.join(unknown)}. Known: {', '.join(bank)}")

    report = ["=== STRUCTURE ==="]
    total_words = sum(len(words(p)) for p in paras)
    report.append(f"Paragraphs: {len(paras)}")
    if stds:
        expected = len(stds) + (0 if args.paragraphs_only else 2)
        report.append(f"Explicit mapping expects {expected} paragraphs.")
        if len(paras) != expected:
            report.append("[WARN] Paragraph count mismatch; the requested mapping may be shifted.")
    lim = f" / maximum {args.limit}" if args.limit is not None else ""
    report.append(f"Approximate words: {total_words}{lim} (Markdown headings and references excluded)")
    failed = args.limit is not None and total_words > args.limit
    if failed:
        report.append(f"[LIMIT] Exceeds the supplied maximum by {total_words - args.limit} words.")
    body = paras if args.paragraphs_only or not stds else paras[1:-1]
    covered = {}
    if stds:
        report.append("\n=== KEYWORD OBSERVATIONS ===")
        report.append("Matches can overlap and do not establish quality, reasoning or a grade. There is no keyword quota.")
    for i, std in enumerate(stds, 1):
        if i > len(body):
            report.append(f"[WARN] No body paragraph for {std}")
            continue
        lines, els = check_paragraph(i, body[i - 1], std, bank, elements)
        for e in els:
            covered.setdefault(e, []).append(std)
        report.extend(lines)
    if args.require_all_elements:
        # Include all relevant paragraphs even when the explicit mapping is incomplete.
        matches = set(elements_named("\n".join(body), elements))
        report.append("\n=== REQUESTED ELEMENT WORDING CHECK ===")
        for e in elements:
            report.append(f"[{'MATCH' if e in matches else 'MISSING'}] {e}")
        failed = failed or len(matches) < len(elements)
        report.append("A wording match does not establish that an element was evaluated. Check the assignment's actual requirements.")
    if args.style:
        report.append("\n=== OPTIONAL STYLE OBSERVATIONS ===")
        report.append("These heuristics do not detect human or AI authorship. Review wording in context.")
        report.extend(pattern_scan(paras))

    report.append("\n=== CLAIMS TO VERIFY ===")
    report.extend(claims(paras, deck_text))
    print("\n".join(report))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
