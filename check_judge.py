#!/usr/bin/env python3
"""Check an AI judge against hand-checked verdicts before trusting its numbers.

Input: a CSV with three columns, id, judge, human. Each row is one item the AI judge
scored, the verdict it gave, and the verdict a careful person gave. Labels are free
text such as pass/fail or yes/no, compared after trimming spaces and ignoring case.

Output: how often the judge agrees with the person, where they disagree, and whether
that clears your threshold. Exit code 0 means usable at the threshold; 1 means not;
2 means bad input: an unreadable file, a malformed CSV, or a bad argument.

    python3 check_judge.py hand_check.csv --min-agreement 0.95
    python3 check_judge.py --selftest
"""
import argparse, collections, csv, sys


class InputError(Exception):
    pass


def load(path):
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as fh:
        reader = csv.DictReader(fh)
        need = {'id', 'judge', 'human'}
        have = {h.strip().lower() for h in (reader.fieldnames or [])}
        if not need <= have:
            raise InputError(f'missing column(s): {", ".join(sorted(need - have))}. Expected: id, judge, human')
        for n, raw in enumerate(reader, start=2):          # line 1 is the header
            row = {k.strip().lower(): (v or '').strip() for k, v in raw.items() if k is not None}
            if not row['judge'] or not row['human']:
                raise InputError(f'line {n}: empty judge or human verdict')
            rows.append((row['id'], row['judge'].lower(), row['human'].lower()))
    if not rows:
        raise InputError('no rows to compare')
    return rows


def compare(rows):
    agree = sum(1 for _, j, h in rows if j == h)
    pairs = collections.Counter((h, j) for _, j, h in rows)
    disagreements = [(i, j, h) for i, j, h in rows if j != h]
    return {'n': len(rows), 'agree': agree, 'rate': agree / len(rows),
            'pairs': pairs, 'disagreements': disagreements}


def short(v, n=80):
    """Verdict text for display: long free-text verdicts are cut so the report stays readable."""
    v = str(v)
    return v if len(v) <= n else v[:n] + '…'


def report(res, threshold):
    out = [f"Agreement: {res['agree']} of {res['n']} ({res['rate']:.1%})", '',
           'Person said -> judge said: count']
    for (h, j), c in sorted(res['pairs'].items()):
        out.append(f'  {short(h)} -> {short(j)}: {c}')
    if res['disagreements']:
        out += ['', 'Disagreements (id, judge, person):']
        out += [f'  {i}: judge={short(j)}, person={short(h)}' for i, j, h in res['disagreements']]
    ok = res['rate'] >= threshold
    out += ['', f"{'USABLE' if ok else 'NOT USABLE'} at the {threshold:.0%} threshold."]
    if not ok:
        out.append('Do not report numbers from this judge until the disagreements are understood and fixed.')
    return '\n'.join(out), ok


def selftest():
    rows = [('a', 'pass', 'pass'), ('b', 'fail', 'pass'), ('c', 'fail', 'fail'), ('d', 'pass', 'pass')]
    res = compare(rows)
    checks = [
        (res['n'] == 4, 'counts all rows'),
        (res['agree'] == 3, 'counts agreements'),
        (abs(res['rate'] - 0.75) < 1e-12, 'computes the agreement rate'),
        (res['disagreements'] == [('b', 'fail', 'pass')], 'lists the disagreement'),
        (res['pairs'][('pass', 'fail')] == 1, 'tallies person-pass, judge-fail'),
        (report(res, 0.95)[1] is False, 'fails a 95% threshold at 75%'),
        (report(res, 0.75)[1] is True, 'passes a 75% threshold at 75%'),
    ]
    bad = [name for ok, name in checks if not ok]
    for ok, name in checks:
        print(('ok  ' if ok else 'FAIL'), name)
    print(f'\n{len(checks) - len(bad)}/{len(checks)} self-tests pass')
    return not bad


def main(argv=None):
    p = argparse.ArgumentParser(description='Check an AI judge against hand-checked verdicts.')
    p.add_argument('csv', nargs='?', help='CSV with columns id, judge, human')
    p.add_argument('--min-agreement', type=float, default=0.95, help='threshold from 0 to 1 (default 0.95)')
    p.add_argument('--selftest', action='store_true', help='run the built-in tests and exit')
    a = p.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if not a.csv:
        p.error('give a CSV file, or --selftest')
    if not 0 <= a.min_agreement <= 1:
        p.error('--min-agreement must be between 0 and 1')
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))   # long free-text verdicts are fine
    try:
        rows = load(a.csv)
    except csv.Error as e:
        print(f'Could not read {a.csv}: not a readable CSV ({e}).', file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print(f'Could not read {a.csv}: the file is not UTF-8 text. Save it as UTF-8 (CSV UTF-8 in Excel) and rerun.', file=sys.stderr)
        return 2
    except (OSError, InputError) as e:
        print(f'Could not read {a.csv}: {e}', file=sys.stderr)
        return 2
    text, ok = report(compare(rows), a.min_agreement)
    print(text)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
