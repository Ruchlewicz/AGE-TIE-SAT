"""AGE-TIE with a sorted list of unsatisfied clauses (bisect updates).
Same RNG calls and clause ordering as matryca_age_tie_production.solve.
Python 3.9+, standard library only.
"""
from bisect import bisect_left, insort
import random
from matryca_age_tie_production import Result, stress


def solve(clauses, initial_state, *, seed=0, budget=24000, p_random=0.5, verify=False):
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
    unsat = [j for j, count in enumerate(counts) if count == 0]
    initial = best = len(unsat)
    best_state = tuple(state)
    last_flip = [-1000000] * n
    flips = 0
    for step in range(budget):
        if not unsat:
            break
        clause = clauses[rng.choice(unsat)]
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
                k = bisect_left(unsat, j)
                assert k < len(unsat) and unsat[k] == j
                unsat.pop(k)
            elif before > 0 and after == 0:
                insort(unsat, j)
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
