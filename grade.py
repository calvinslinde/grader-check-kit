#!/usr/bin/env python3
"""Answer normalisation + equivalence. Unit-tested; do not patch blind."""
import re
from fractions import Fraction

def extract(txt):
    txt = txt or ""
    m = re.findall(r"FINAL\s*:\s*(.+)", txt, re.I)
    got = m[-1] if m else ((txt.strip().splitlines() or [""])[-1])
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
]
if __name__ == "__main__":
    bad = 0
    for got, gold, want in TESTS:
        g = same(got, gold)
        flag = "ok " if g == want else "FAIL"
        if g != want: bad += 1
        print(f"{flag} same({got!r:<26}, {gold!r:<12}) = {g}  (want {want})  norm->{norm(extract(got))!r}")
    print(f"\n{len(TESTS)-bad}/{len(TESTS)} grader tests pass")
