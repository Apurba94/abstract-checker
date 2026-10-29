"""Command-line interface for abstract-checker."""
import argparse
import json
import re
import sys

from .core import check_abstract


def extract_abstract(text):
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.S)
    if m:
        body = re.sub(r"(?<!\\)%.*", " ", m.group(1)).replace("\\%", "%")
        return re.sub(r"\\[a-zA-Z]+\*?(\{[^}]*\})?", " ", body)
    m = re.search(r"^#+\s*abstract\s*$(.*?)(?=^#|\Z)", text, re.S | re.I | re.M)
    return m.group(1) if m else text


def main(argv=None):
    ap = argparse.ArgumentParser(prog="abstract-checker", description="Check an abstract's structure and completeness.")
    ap.add_argument("file", nargs="?", help=".txt/.md/.tex file (abstract is extracted); stdin if omitted")
    ap.add_argument("-w", "--word-limit", type=int, default=250)
    ap.add_argument("--require", default="background,methods,results,conclusion",
                    help="comma-separated components that must be present")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--show", action="store_true", help="show the component assigned to each sentence")
    args = ap.parse_args(argv)
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
    else:
        text = sys.stdin.read()
    res = check_abstract(extract_abstract(text), args.word_limit, [c for c in args.require.split(",") if c])
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print("%d words, %d sentences; components found: %s" % (res["words"], res["sentences"], ", ".join(res["components"])))
        if args.show:
            for comp, sc, s in res["labels"]:
                print("  [%-10s] %s" % (comp if sc else "?", s[:100]))
        for sev, code, msg in res["issues"]:
            print("%-7s %-18s %s" % (sev, code, msg))
    return 1 if any(i[0] == "error" or i[1].startswith("missing") for i in res["issues"]) else 0
