#!/usr/bin/env python3
"""Answer normalisation + equivalence. Unit-tested; do not patch blind."""
import re, sys
from fractions import Fraction

# Markers in order of precedence. The highest-precedence marker that appears anywhere wins,
# and the text after its LAST occurrence is used (found by position, so an earlier marker's
# capture cannot swallow a later one). "FINAL: 40 ... the answer is correct" gives 40.
MARKERS = [
    r"FINAL\s*:",
    r"final\s+answer\s*(?:is\b\s*:?|:)",   # needs ':' or 'is', so "the final answer." is not a marker
    r"\banswer\s*(?:is\b\s*:?|:)",          # same; "This answer assumes" is not a marker
]
_STARTS = [re.compile("(?=" + m + ")", re.I) for m in MARKERS]
_FULL = [re.compile(m + r"\s*(.*)", re.I) for m in MARKERS]

def extract(txt):
    """The final answer: the text after the last 'FINAL:'; failing that, after the last
    'final answer:' or 'final answer is'; failing that, after the last 'answer:' or 'answer is'
    (any case). With no marker, the last non-empty line. A bare equation such as 'x = 40' is not a marker."""
    txt = txt or ""
    got = None
    for starts, full in zip(_STARTS, _FULL):
        positions = [m.start() for m in starts.finditer(txt)]
        if positions:
            got = full.match(txt, positions[-1]).group(1)
            break
    if got is None:
        lines = [l for l in txt.strip().splitlines() if l.strip()]
        got = lines[-1] if lines else ""
    parts = re.split(r"(\.\s+)(?=[A-Za-z])", got, maxsplit=1)   # ["$40$", ". ", "I hope it is correct."]
    if len(parts) == 3 and value(norm(parts[0])) is not None:
        got = parts[0]        # "$40$. I hope it is correct." -> "$40$"; "Mt. Everest" is left alone
    got = re.sub(r"</?[A-Za-z][^>]*>", " ", got)      # strip <answer> ... </answer>
    got = got.replace("<", " ").replace(">", " ")      # strip stray brackets
    return got.strip()

def norm(s):
    s = (s or "").strip().lower()
    s = s.replace("\u2212", "-")                    # Unicode minus sign (U+2212) -> ASCII hyphen-minus
    s = re.sub(r"</?[a-z][^>]*>", " ", s)
    s = re.sub(r"\\boxed\s*\{([^{}]*)\}", r"\1", s)
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = re.sub(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"(\1)/(\2)", s)
    s = s.replace("√", "sqrt")
    s = re.sub(r"\\?sqrt\s*\{?\s*(\d+)\s*\}?", r"sqrt(\1)", s)
    s = re.sub(r"[\\$,*_]|\\\(|\\\)|\\\[|\\\]", "", s)
    s = re.sub(r"\b(the|answer|is|approximately|approx|about|equals|mph|dollars?|cents?|people|persons?|years?|old|hours?|litres?|liters?)\b", " ", s)
    s = s.replace("·", "*").replace("×", "*").replace("≈", "")
    s = re.sub(r"\s+", "", s)
    s = s.strip(".")
    s = re.sub(r"\((-?\d+)\)/\((\d+)\)", r"\1/\2", s)   # (99)/(100) -> 99/100
    if s.startswith("(") and s.endswith(")") and s.count("(") == 1 and s.count(")") == 1:
        s = s[1:-1]                                   # unwrap a genuinely single outer paren
    s = re.sub(r"^(-?\d+)\.0+$", r"\1", s)
    return s

def value(s):
    """Numeric value of a normalised answer, or None."""
    try:
        if re.fullmatch(r"-?\d+", s): return float(s)
        if re.fullmatch(r"-?\d*\.\d+", s): return float(s)
        m = re.fullmatch(r"(-?\d+)/(\d+)", s)
        if m: return float(Fraction(int(m.group(1)), int(m.group(2))))
        m = re.fullmatch(r"(-?\d*)\*?sqrt\((\d+)\)", s)
        if m:
            k = m.group(1)
            k = -1.0 if k == "-" else (1.0 if k in ("", "+") else float(k))
            return k * float(m.group(2)) ** 0.5
        m = re.fullmatch(r"sqrt\((\d+)\)/(\d+)", s)
        if m: return float(m.group(1))**0.5 / float(m.group(2))
    except Exception: pass
    return None

def same(got, gold):
    a, b = norm(extract(got)), norm(gold)
    if a == b: return True
    if not a: return False
    va, vb = value(a), value(b)
    if va is not None and vb is not None: return abs(va - vb) < 1e-6
    return False

TESTS = [
 ("<answer>1/11</answer>", "1/11", True),
 ("FINAL: <5\\sqrt{2}>", "5*sqrt(2)", True),
 ("5sqrt2", "5*sqrt(2)", True),
 ("5\\sqrt2", "5*sqrt(2)", True),
 ("$\\boxed{40}$", "40", True),
 ("The answer is 40 mph", "40", True),
 ("\\frac{99}{100}", "99/100", True),
 ("36/7", "36/7", True),
 ("5.142857", "36/7", True),
 ("160.00", "160", True),
 ("nurse", "nurse", True),
 ("41", "40", False),
 ("", "40", False),
 ("1/6", "1/11", False),
 ("7.0710678", "5*sqrt(2)", True),
 ("5\u221a2", "5*sqrt(2)", True),
 ("<answer>5\u221a2</answer>", "5*sqrt(2)", True),
 ("\u221a2/2", "sqrt(2)/2", True),
 # Added for the public release: the Unicode minus sign, the same class of bug as the Unicode √.
 ("\u22123/4", "-3/4", True),
 ("\u22120.75", "-3/4", True),
 ("(\u22123)/(4)", "-3/4", True),
 ("\u22123/4", "3/4", False),
 # added after a fresh-user test (2026-10-18): common answer phrasings
 ("Answer: 40", "40", True),
 ("Final answer: 40", "40", True),
 ("The answer is 40.\nHope that helps!", "40", True),
 ("the answer is: 1/2", "0.5", True),
 ("x = 40", "40", False),        # documented limit: a bare equation is not a marker
 # added after the re-test (2026-10-18): precedence and more phrasings
 ("FINAL: 40\nThe answer is correct.", "40", True),
 ("The final answer is 40.", "40", True),
 ("Final answer is 1/2", "0.5", True),
 ("the answer is correct", "40", False),
 # added after the final check (2026-10-18): a later plain "answer" must not take over
 ("Answer: 40\nThis answer assumes whole numbers.", "40", True),
 ("Answer: 40\nI answered with the formula from step 2.", "40", True),
 ("The answer is 40.\nThis answer uses the formula above.", "40", True),
 ("Let me check my work before giving the final answer.\nAnswer: 40", "40", True),
 ("Final Answer: The final answer is $40$. I hope it is correct.", "40", True),
 ("FINAL: 3.5", "7/2", True),
 # added after the last check (2026-10-18): the trailing-sentence cut must not split abbreviations
 ("Answer: Mt. Everest", "Mt. Everest", True),
 ("Answer: St. Louis", "St. Louis", True),
 ("Answer: Dr. Smith", "Dr. Smith", True),
]
if __name__ == "__main__":
    bad = 0
    for got, gold, want in TESTS:
        g = same(got, gold)
        flag = "ok " if g == want else "FAIL"
        if g != want: bad += 1
        print(f"{flag} same({got!r:<26}, {gold!r:<12}) = {g}  (want {want})  norm->{norm(extract(got))!r}")
    print(f"\n{len(TESTS)-bad}/{len(TESTS)} grader tests pass")
    sys.exit(1 if bad else 0)
