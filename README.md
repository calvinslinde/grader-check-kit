# Check your AI grader before you trust its numbers

If a program scores your AI's answers, the scores are only as good as that program. A grader that mishandles one answer format will report a capability the model doesn't have, or hide one it does.

This kit has two small tools and one habit.

## The habit

1. **Write down what the grader must do before you score anything.** Use pairs of a model answer and a correct answer, each marked "should match" or "should not match."
2. **Use the formats models actually produce.** That means answer tags, LaTeX, Unicode symbols, units, trailing zeros, and "the answer is" phrasing.
3. **Include answers that must fail.** Near misses, wrong fractions, empty answers.
4. **Run the tests every time you change the grader.** Never patch it blind.
5. **If an AI judges open-ended answers, check it against a careful person first.** Score a sample by hand, compare, and only then trust the judge's numbers.
6. **Keep overturned results on the record.** A results log that quietly deletes its own errors can't be trusted.

## Where this comes from

In the project this kit is drawn from, four bugs in the grader had each made a model look more capable than it was. Every headline number before the fix was false:

- angle brackets left over from the prompt template;
- answer tags that weren't stripped;
- a bare `sqrt2`;
- a Unicode `√` replaced only after the square-root rule had already run.

The grader was rebuilt with 18 unit tests. Separately, once the AI judge was checked against careful re-scoring, 17 of 42 earlier verdicts flipped.

## The tools

### `grade.py`: answer matching, with its tests built in

It pulls the final answer out of a model's output, normalizes it (tags, LaTeX fractions, square roots, units, filler words), and compares it to the correct answer, by number when both parse as numbers.

```
python3 grade.py
```

This runs the 22 built-in tests: the original 18, plus 4 added for this release. The additions cover the Unicode minus sign `−`, the same class of bug as the Unicode `√`. Add your own cases to `TESTS` before you rely on it.

Use it in your code:

```python
from grade import same
same("FINAL: <5\\sqrt{2}>", "5*sqrt(2)")   # True
```

### `check_judge.py`: is the AI judge usable?

Make a CSV with columns `id,judge,human`: one row per item, the judge's verdict, and a careful person's verdict. Then run:

```
python3 check_judge.py example/hand_check.csv --min-agreement 0.95
```

It prints the agreement rate, a person-versus-judge tally, and every disagreement. Then it says USABLE or NOT USABLE at your threshold. The exit code is 0 for usable, 1 for not usable, and 2 for bad input, so it can gate an automated pipeline. Run `python3 check_judge.py --selftest` to check the tool itself.

## What it can't do

- `grade.py` handles numbers, fractions, square roots, and short text answers. It does not understand percentages (`40%` does not match `40`), scientific notation (`1e-3`), comma decimals (`1,5` becomes `15`), units it doesn't list, or answers that need reasoning to compare. Add tests for your formats, and extend it when they fail.
- `check_judge.py` measures agreement; it doesn't tell you *why* the judge disagrees. Read every disagreement.
- Neither replaces looking at the outputs yourself.

## Requirements

Python 3.8 or newer. Standard library only.

## License

MIT. See `LICENSE`.
