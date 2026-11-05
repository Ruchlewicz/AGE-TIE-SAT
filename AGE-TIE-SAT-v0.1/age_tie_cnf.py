"""DIMACS 3-CNF command-line adapter for the unchanged AGE-TIE FAST solver.
Python 3.9+, standard library only.
"""
import argparse
import random
from pathlib import Path
from age_tie_fast import solve
from matryca_age_tie_production import stress


def read_dimacs(path):
    header = None
    tokens = []
    for line_no, raw in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('c') or line.startswith('%'):
            continue
        if line.startswith('p'):
            if header is not None:
                raise ValueError('Duplicate DIMACS header')
            parts = line.split()
            if len(parts) != 4 or parts[1] != 'cnf':
                raise ValueError('Expected: p cnf VARIABLES CLAUSES')
            n, m = int(parts[2]), int(parts[3])
            if n < 0 or m < 0:
                raise ValueError('Negative DIMACS size')
            header = (n, m)
        else:
            if header is None:
                raise ValueError(f'Clause data before header at line {line_no}')
            tokens.extend(int(t) for t in line.split())
    if header is None:
        raise ValueError('Missing DIMACS header')
    n, m = header
    clauses, clause = [], []
    for lit in tokens:
        if lit == 0:
            if len(clause) != 3 or len({abs(x) for x in clause}) != 3:
                raise ValueError('AGE-TIE FAST supports only 3 distinct variables per clause')
            clauses.append(tuple(clause))
            clause = []
        else:
            if abs(lit) > n:
                raise ValueError('Literal exceeds declared variable count')
            clause.append(lit)
    if clause or len(clauses) != m:
        raise ValueError('Clause count mismatch or unterminated clause')
    return n, clauses


def main():
    ap = argparse.ArgumentParser(description='AGE-TIE FAST for strict DIMACS 3-CNF')
    ap.add_argument('file', help='DIMACS .cnf file')
    ap.add_argument('--budget', type=int, default=10000)
    ap.add_argument('--starts', type=int, default=10)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--p-random', type=float, default=0.5)
    args = ap.parse_args()
    if args.starts < 1:
        ap.error('--starts must be >= 1')
    try:
        n, clauses = read_dimacs(args.file)
        best = None
        for i in range(args.starts):
            rng = random.Random(args.seed + 2*i)
            state = tuple(bool(rng.getrandbits(1)) for _ in range(n))
            result = solve(clauses, state, seed=args.seed + 2*i + 1,
                           budget=args.budget, p_random=args.p_random)
            if stress(clauses, result.best_state) != result.best_stress:
                raise RuntimeError('Solution verification failed')
            if best is None or result.best_stress < best.best_stress:
                best = result
            if result.solved:
                break
        if best.solved:
            print('s SATISFIABLE')
            for k in range(0, n, 15):
                print('v ' + ' '.join(str(j+1 if best.best_state[j] else -(j+1))
                                    for j in range(k, min(k+15, n))) + ' 0')
        else:
            print('s UNKNOWN')
        print(f'c best_stress={best.best_stress} starts_used={i+1} budget={args.budget}')
    except (OSError, ValueError) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    main()
