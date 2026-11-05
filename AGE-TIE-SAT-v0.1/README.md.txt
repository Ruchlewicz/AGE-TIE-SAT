AGE-TIE SAT v0.1

Project creator: Rafał Ruchlewicz
Development: Rafał Ruchlewicz with AI assistance
Status: Experimental research prototype

About

AGE-TIE SAT is an experimental stochastic local-search solver for Boolean satisfiability problems (3-SAT).

The solver combines randomized moves, local stress minimization, age-based tie-breaking, and preservation of the best assignment encountered.

The project explores whether these mechanisms can improve practical search efficiency.

Project files

age_tie_fast.py — AGE-TIE solver core

matryca_age_tie_production.py — supporting functions

age_tie_cnf.py — DIMACS CNF command-line interface

test_sat_tool_03.py — automated correctness tests

age_tie_demo.cnf — satisfiable example

age_tie_unsat_demo.cnf — unsatisfiable example

Requirements

Python 3.

Usage

Run a sample SAT instance:

python age_tie_cnf.py age_tie_demo.cnf

Run the automated tests:

python test_sat_tool_03.py

Supported input

The current interface supports DIMACS CNF formulas with exactly three distinct variables per clause.

Output

SATISFIABLE — a satisfying assignment was found and verified.

UNKNOWN — no satisfying assignment was found within the search budget.

UNKNOWN does not mean UNSAT. This solver does not prove unsatisfiability.

Validation

SAT-TOOL-03 testing included:

80 random small instances checked against an exhaustive brute-force oracle.

A known unsatisfiable example.

Six invalid-input cases.

The reported test run passed without false SAT claims.

These results are preliminary and do not establish superiority over state-of-the-art SAT solvers.

Research direction

Future work includes reproducible benchmarking against established SAT solvers, further evaluation of the age-based tie-breaking heuristic, and practical applications.

Attribution

Project concept, experimental direction, and evaluation decisions: Rafał Ruchlewicz.

Implementation, debugging, and documentation developed with AI assistance.

The project builds on established stochastic local-search ideas. Algorithmic novelty has not yet been independently established.## Feedback and collaboration

If you use AGE-TIE in research, experiments, or practical applications, I would appreciate hearing about your results.

Bug reports, suggestions, benchmark results, and contributions are welcome. Please open a GitHub Issue or start a Discussion to share your feedback.