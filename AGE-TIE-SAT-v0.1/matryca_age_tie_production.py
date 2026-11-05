"""Matryca AGE-TIE: standalone reproducible experimental 3-SAT local search.

This is the incremental experimental engine from Test 40, NOT the distinct
historical matryca_v1.solve implementation. Python >=3.9; stdlib only.
"""
from __future__ import annotations
from dataclasses import dataclass
import argparse
import csv
import random

@dataclass(frozen=True)
class Result:
    best_state: tuple[bool, ...]
    best_stress: int
    initial_stress: int
    flips: int
    solved: bool


def stress(clauses, state):
    return sum(not any(state[abs(lit)-1] == (lit > 0) for lit in clause)
               for clause in clauses)


def generate(nvars=200, nclauses=852, seed=0):
    if nvars < 3 or nclauses < 0:
        raise ValueError('nvars >= 3 and nclauses >= 0 required')
    rng = random.Random(seed)
    clauses = []
    for _ in range(nclauses):
        vs = rng.sample(range(1, nvars + 1), 3)
        clauses.append(tuple(v * rng.choice((-1, 1)) for v in vs))
    state = tuple(bool(rng.getrandbits(1)) for _ in range(nvars))
    return clauses, state


def solve(clauses, initial_state, *, seed=0, budget=24000, p_random=0.5,
          verify=False):
    """Random unsat clause; random literal with p_random, else min delta,
    tie broken by oldest last flip; remaining ties uniformly random.
    The initial state is not mutated. A best-state snapshot is retained.
    """
    if budget < 0 or not (0 <= p_random <= 1):
        raise ValueError('invalid budget or probability')
    state = list(initial_state)
    n = len(state)
    for clause in clauses:
        if len(clause) != 3 or any(abs(l) < 1 or abs(l) > n for l in clause):
            raise ValueError('requires 3-literal clauses with valid indices')
        if len({abs(l) for l in clause}) != 3:
            raise ValueError('repeated variable in a clause is unsupported')
    rng = random.Random(seed)
    adj = [[] for _ in range(n)]
    for j, clause in enumerate(clauses):
        for lit in clause:
            adj[abs(lit)-1].append((j, lit > 0))
    counts = [sum(state[abs(l)-1] == (l > 0) for l in c) for c in clauses]
    unsat = {j for j, count in enumerate(counts) if count == 0}
    initial = best = len(unsat)
    best_state = tuple(state)
    last_flip = [-1000000] * n
    flips = 0
    for step in range(budget):
        if not unsat:
            break
        # Preserve Test 40's sorted-set sampling and RNG consumption.
        clause = clauses[rng.choice(tuple(sorted(unsat)))]
        if rng.random() < p_random:
            lit = rng.choice(clause)
        else:
            scored = []
            for lit0 in clause:
                ix = abs(lit0)-1
                old = state[ix]
                delta = 0
                for j, positive in adj[ix]:
                    before = counts[j]
                    after = before + (1 if old != positive else -1)
                    delta += (after == 0) - (before == 0)
                scored.append((delta, lit0))
            minimum = min(delta for delta, _ in scored)
            tied = [l for delta, l in scored if delta == minimum]
            oldest = min(last_flip[abs(l)-1] for l in tied)
            tied = [l for l in tied if last_flip[abs(l)-1] == oldest]
            lit = rng.choice(tied)
        ix = abs(lit)-1
        old = state[ix]
        state[ix] = not old
        for j, positive in adj[ix]:
            before = counts[j]
            after = before + (1 if old != positive else -1)
            counts[j] = after
            if before == 0 and after > 0:
                unsat.remove(j)
            elif before > 0 and after == 0:
                unsat.add(j)
        last_flip[ix] = step
        flips += 1
        if len(unsat) < best:
            best = len(unsat)
            best_state = tuple(state)
        if verify:
            assert all(counts[j] == sum(state[abs(l)-1] == (l > 0) for l in c)
                       for j, c in enumerate(clauses))
            assert len(unsat) == stress(clauses, state)
            assert stress(clauses, best_state) == best
    assert stress(clauses, best_state) == best
    return Result(best_state, best, initial, flips, best == 0)


def replay_csv(path):
    """Replay AGE-TIE rows from Test 40; generator SAT certificates
    are not re-checked here (requires external Z3)."""
    checked = 0
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            if row['variant'] != 'age_tie':
                continue
            clauses, initial = generate(200, 852, int(row['generator_seed']))
            result = solve(clauses, initial, seed=int(row['walk_seed']))
            assert result.best_stress == int(row['best']), row
            assert result.flips == int(row['flips']), row
            assert result.solved == bool(int(row['solved'])), row
            checked += 1
    return checked


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', help='Test 40 results CSV')
    parser.add_argument('--n', type=int, default=200)
    parser.add_argument('--m', type=int, default=852)
    parser.add_argument('--instance-seed', type=int, default=404000000)
    parser.add_argument('--walk-seed', type=int, default=405000000)
    parser.add_argument('--budget', type=int, default=24000)
    args = parser.parse_args()
    if args.replay:
        print('Verified AGE-TIE rows:', replay_csv(args.replay))
    else:
        clauses, initial = generate(args.n, args.m, args.instance_seed)
        result = solve(clauses, initial, seed=args.walk_seed, budget=args.budget)
        print(result)
        print('best_state_verified:', stress(clauses, result.best_state) == result.best_stress)
