"""SAT-TOOL-03: deterministic exhaustive-oracle CLI regression tests."""
import itertools
import random
import io
import contextlib
import age_tie_cnf
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLI = ROOT / 'age_tie_cnf.py'
RNG = random.Random(20261105)


def satisfiable(n, clauses):
    return any(all(any((state[abs(l)-1] if l > 0 else not state[abs(l)-1]) for l in clause)
                   for clause in clauses)
               for state in itertools.product((False, True), repeat=n))


def run_file(path, *args):
    out, err = io.StringIO(), io.StringIO()
    old_argv = sys.argv
    code = 0
    try:
        sys.argv = [str(CLI), str(path), *args]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                age_tie_cnf.main()
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.argv = old_argv
    return type('RunResult', (), {'returncode': code, 'stdout': out.getvalue(), 'stderr': err.getvalue()})()


def check_case(path, n, clauses, expected_sat, *args):
    result = run_file(path, *args)
    assert result.returncode == 0, (path, result.stderr)
    lines = result.stdout.splitlines()
    status = [line for line in lines if line.startswith('s ')]
    assert len(status) == 1, (path, result.stdout)
    assert status[0] in ('s SATISFIABLE', 's UNKNOWN'), status
    if status[0] == 's SATISFIABLE':
        assert expected_sat, ('FALSE SAT', path)
        lits = []
        for line in lines:
            if line.startswith('v '):
                values = list(map(int, line.split()[1:]))
                assert values[-1] == 0
                lits.extend(values[:-1])
        assert len(lits) == n and {abs(l) for l in lits} == set(range(1, n+1)), (path, lits)
        state = tuple(l > 0 for l in lits)
        assert all(any(state[abs(l)-1] == (l > 0) for l in c) for c in clauses), ('BAD WITNESS', path)
    return status[0]


def main():
    counts = {'sat': 0, 'unsat': 0, 'sat_found': 0, 'unknown_sat': 0, 'unknown_unsat': 0}
    with tempfile.TemporaryDirectory(prefix='age_tie_sat_tool_') as tmp:
        tmp = Path(tmp)
        for case in range(80):
            n = RNG.randint(3, 7)
            m = RNG.randint(0, 4*n+5)
            clauses = []
            for _ in range(m):
                vs = RNG.sample(range(1, n+1), 3)
                clauses.append(tuple(v if RNG.getrandbits(1) else -v for v in vs))
            oracle = satisfiable(n, clauses)
            path = tmp / ('case_%03d.cnf' % case)
            # Split a few clauses over multiple lines to check tokenization.
            parts = [f'c case {case}', f'p cnf {n} {m}']
            for c in clauses:
                if case % 7 == 0:
                    parts.extend((f'{c[0]} {c[1]}', f'{c[2]} 0'))
                else:
                    parts.append(' '.join(map(str, c)) + ' 0')
            path.write_text('\n'.join(parts) + '\n', encoding='utf-8')
            status = check_case(path, n, clauses, oracle, '--budget', '250', '--starts', '2', '--seed', str(100+case))
            counts['sat' if oracle else 'unsat'] += 1
            if oracle and status == 's SATISFIABLE':
                counts['sat_found'] += 1
            elif oracle:
                counts['unknown_sat'] += 1
            else:
                counts['unknown_unsat'] += 1
        # Contradictory complete 3-variable instance.
        unsat_clauses = list(itertools.product((1, -1), (2, -2), (3, -3)))
        path = tmp / 'known_unsat.cnf'
        path.write_text('p cnf 3 8\n' + ''.join(' '.join(map(str, c))+' 0\n' for c in unsat_clauses))
        assert check_case(path, 3, unsat_clauses, False, '--budget', '1000', '--starts', '3') == 's UNKNOWN'
        # Malformed input must be rejected.
        invalid = ['p cnf 3 1\n1 2 0\n', 'p cnf 3 1\n1 1 2 0\n',
                   'p cnf 3 1\n1 2 4 0\n', 'p cnf 3 2\n1 2 3 0\n',
                   'p cnf 3 1\n1 2 3\n', '1 2 3 0\n']
        for idx, body in enumerate(invalid):
            path = tmp / f'invalid_{idx}.cnf'
            path.write_text(body)
            result = run_file(path)
            assert result.returncode != 0, ('ACCEPTED INVALID INPUT', idx, result.stdout)
    print('SAT-TOOL-03: PASS')
    print('80 random cases + 1 known UNSAT + 6 invalid inputs')
    print('Exact brute-force oracle for N=3..7')
    print('SAT formulas:', counts['sat'], '| solutions found:', counts['sat_found'], '| UNKNOWN:', counts['unknown_sat'])
    print('UNSAT formulas:', counts['unsat'], '| correctly UNKNOWN:', counts['unknown_unsat'])
    print('False SAT claims: 0 | Invalid inputs accepted: 0')


if __name__ == '__main__':
    main()
