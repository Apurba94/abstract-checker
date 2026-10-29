"""Cue-phrase classification of abstract sentences into IMRaD components plus rule checks."""
import re

COMPONENTS = ("background", "objective", "methods", "results", "conclusion")

CUES = {
    "background": [r"\bremains? (?:unclear|unknown|poorly)", r"\blittle is known", r"\bhowever\b", r"\bis (?:a|an|one of)\b",
                   r"\bhas (?:been|become)\b", r"\bincreasingly\b", r"\bcommon\b", r"\bchalleng", r"\bimportant\b",
                   r"\bgap\b", r"\blimited\b", r"\bprevious(?:ly)?\b"],
    "objective": [r"\b(?:we|this (?:study|paper|work|article)) (?:aim|aimed|seek|sought|investigat|examin|explor|propos|present|introduc)",
                  r"\b(?:aim|objective|purpose|goal) (?:of|was|is)\b", r"\bto (?:investigate|examine|assess|evaluate|determine)\b",
                  r"\bhere,? we\b", r"\bin this (?:study|paper|work)\b"],
    "methods": [r"\bwe (?:used|conducted|performed|collected|analy[sz]ed|recruited|trained|developed|surveyed|interviewed|designed|applied)",
                r"\b(?:data|samples|participants|patients) (?:were|was)\b", r"\brandomi[sz]ed\b", r"\bcohort\b",
                r"\bregression\b", r"\bsurvey\b", r"\bdataset\b", r"\bn\s*=\s*\d", r"\busing\b", r"\bmethod", r"\bexperiment"],
    "results": [r"\bwe (?:found|observed|show|showed|demonstrate|identified|report)", r"\bresults? (?:show|showed|indicate|revealed)",
                r"\bp\s*[<=>]\s*0?\.\d", r"\b\d+(?:\.\d+)?\s*%", r"\b(?:increased|decreased|reduced|improved|outperform)",
                r"\bsignificant(?:ly)?\b", r"\b95\s*%\s*CI\b", r"\b(?:odds|hazard|risk) ratio\b", r"\baccuracy of\b"],
    "conclusion": [r"\b(?:we conclude|in conclusion|these (?:findings|results) (?:suggest|indicate|highlight|show))",
                   r"\bimplications?\b", r"\bfuture (?:work|research|studies)\b", r"\bcould (?:help|inform|be used)\b",
                   r"\bsuggest(?:s|ing)? that\b", r"\bunderscore", r"\bhighlight", r"\bpave"],
}
HEADINGS = {"background": r"background|introduction|context|purpose", "objective": r"objectives?|aims?",
            "methods": r"methods?|design|setting|materials and methods|approach",
            "results": r"results?|findings", "conclusion": r"conclusions?|interpretation|implications"}
_COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in CUES.items()}


def split_sentences(text):
    t = re.sub(r"\s+", " ", text.strip())
    t = re.sub(r"\b(e\.g|i\.e|et al|vs|approx|Fig|ca)\.", lambda m: m.group(0).replace(".", "\u2024"), t)
    t = re.sub(r"(\d)\.(\d)", "\\1\u2024\\2", t)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", t)
    return [p.replace("\u2024", ".") for p in parts if p.strip()]


def classify_sentence(sentence, position=0.5):
    """Return (component, score). Position (0..1 in the abstract) breaks ties."""
    scores = {k: sum(1 for rx in rxs if rx.search(sentence)) for k, rxs in _COMPILED.items()}
    prior = {"background": 1 - position, "objective": 1 - abs(position - 0.25) * 2,
             "methods": 1 - abs(position - 0.45) * 2, "results": 1 - abs(position - 0.7) * 2,
             "conclusion": position}
    best = max(COMPONENTS, key=lambda k: (scores[k] + 0.3 * prior[k], -COMPONENTS.index(k)))
    return best, scores[best]


def _structured(text):
    pat = re.compile(r"(?:^|\n|\s)(%s)\s*:" % "|".join("(?:%s)" % h for h in HEADINGS.values()), re.I)
    found = []
    for m in pat.finditer(text):
        word = m.group(1).lower()
        for comp, h in HEADINGS.items():
            if re.fullmatch(h, word):
                found.append(comp)
                break
    return found


def check_abstract(text, word_limit=250, require=("background", "methods", "results", "conclusion")):
    words = re.findall(r"[A-Za-z0-9][\w'\-]*", text)
    sents = split_sentences(text)
    labels = []
    for i, s in enumerate(sents):
        comp, sc = classify_sentence(s, i / max(1, len(sents) - 1))
        labels.append((comp, sc, s))
    structured = _structured(text)
    present = set(structured) | {c for c, sc, _ in labels if sc > 0}
    issues = []
    if len(words) > word_limit:
        issues.append(("error", "over-limit", "%d words exceeds the limit of %d" % (len(words), word_limit)))
    for comp in require:
        if comp not in present:
            issues.append(("warning", "missing-" + comp, "no sentence clearly reports the %s" % comp))
    if not re.search(r"\d", text):
        issues.append(("warning", "no-numbers", "no quantitative results (numbers, effect sizes, p-values)"))
    if re.search(r"\[\d+(?:[,\-\u2013]\s*\d+)*\]|\\cite|\(\w+(?: et al\.)?,? \d{4}\)", text):
        issues.append(("warning", "citation", "abstracts should not contain citations"))
    if re.search(r"\b(?:Fig(?:ure)?s?\.?|Table)\s*\d", text):
        issues.append(("warning", "figure-ref", "abstracts should not refer to figures or tables"))
    if sents and len(re.findall(r"\w+", max(sents, key=len))) > 40:
        issues.append(("info", "long-sentence", "a sentence has more than 40 words"))
    order = [COMPONENTS.index(c) for c, sc, _ in labels if sc > 0]
    if any(b < a - 1 for a, b in zip(order, order[1:])):
        issues.append(("info", "order", "components appear out of the usual order"))
    return {"words": len(words), "sentences": len(sents), "structured_headings": structured,
            "components": sorted(present, key=COMPONENTS.index), "labels": labels, "issues": issues}
