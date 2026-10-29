# abstract-checker

**Check whether your abstract tells the whole story (background, objective, methods,
results, conclusion) within the word limit, with numbers, and without citations or figure references.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

The abstract is the most-read part of a paper and the basis of most screening decisions in
peer review and systematic reviews. Reporting guidelines (CONSORT, PRISMA, STROBE for abstracts)
expect each IMRaD component and concrete quantitative results. Common faults are easy to detect
automatically: missing methods or results, no numbers, citations, "see Figure 2", over-length.

## Features

- Sentence-level classification into background / objective / methods / results / conclusion
  using transparent cue phrases plus position priors
- Recognizes structured abstracts (`Background:`, `Methods:` ...)
- Checks word limit, missing components, quantitative content, citations, figure/table references,
  very long sentences and component order
- Extracts the abstract from LaTeX (`abstract` environment) or Markdown (`# Abstract`)
- `--show` prints the label of every sentence; JSON output; exit code 1 on errors or missing parts

## Usage

```bash
pip install .
abstract-checker abstract.txt -w 200
abstract-checker paper.tex --show
echo "..." | abstract-checker --require methods,results
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
