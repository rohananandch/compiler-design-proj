# Regex to Minimized DFA Automaton Studio

> **An End-to-End Compiler Design Tool**: Transforms Regular Expressions into Minimized Deterministic Finite Automata (DFA) using Thompson's Construction, Subset Construction, and Hopcroft's Algorithm, complete with state reduction analytics and an interactive web visualizer.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Dependencies](https://img.shields.io/badge/dependencies-0%20external-brightgreen.svg)]()

---

## Architecture & System Pipeline

```
[Input Regex] ➔ [Regex Parser] ➔ [NFA Construction] ➔ [DFA Conversion] ➔ [DFA Minimization] ➔ [State Comparison Report]
```

1. **Regex Parser & Shunting-Yard**: Validates operator syntax, inserts explicit concatenation operators (`.`), and converts infix expressions into Reverse Polish Notation (postfix).
2. **Thompson's Construction (NFA)**: Synthesizes a non-deterministic state machine using stack operations and $\epsilon$-transitions with single start and accept states.
3. **Subset Construction (DFA)**: Converts the NFA to an equivalent deterministic finite automaton by computing $\epsilon$-closures and move sets.
4. **Hopcroft's Minimization**: Merges indistinguishable states via partition refinement in $O(|\Sigma| \cdot n \log n)$ time.
5. **State Reduction Analyzer**: Computes state and transition savings (%) and execution latencies across each transformation phase.
6. **String Simulator**: Validates input string acceptance and verifies step-by-step state traces across all three automata.

---

## Quickstart

### 1. Launch the Interactive Web Visualizer
Run the built-in HTTP server (zero external pip packages required):

```bash
python server.py 8080
```
Then open your browser at:
👉 **[http://localhost:8080](http://localhost:8080)**

### 2. Command-Line Interface (CLI)
Run directly from your terminal:

```bash
# Convert a regex and display ASCII transition tables & state reduction report
python main.py "(a|b)*abb"

# Test strings with ground truth simulation
python main.py "(a|b)*abb" --simulate "abb" "ababb" "ba" "a"

# Export Graphviz DOT files (.dot) for external rendering
python main.py "(a|b)*abb" --export-dot

# Interactive REPL mode
python main.py --interactive
```

### 3. Run the Unit Test Suite
Run 19 automated tests covering syntax validation, NFA construction, powerset conversion, Hopcroft minimization, and Python `re` ground-truth matching:

```bash
python -m unittest discover tests
```

---

## Benchmark Examples

| Regular Expression | Description | NFA States | DFA States | Min DFA States | State Reduction |
|--------------------|-------------|------------|------------|----------------|-----------------|
| `(a\|b)*abb` | Classic tokens ending in `abb` | 14 | 5 | 4 | **71.43%** |
| `(a\|b)*a(a\|b)` | Second-to-last character is `a` | 12 | 4 | 4 | **66.67%** |
| `a(b\|c)*` | Identifier prefix with alternatives | 8 | 3 | 3 | **62.50%** |
| `(0\|1)*00(0\|1)*` | Binary strings containing `00` | 16 | 4 | 4 | **75.00%** |
| `a*b*` | Consecutive Kleene stars | 8 | 3 | 3 | **62.50%** |

---

## Project Structure

```
compler design proj/
├── regex_to_dfa/
│   ├── __init__.py           # Package exports
│   ├── parser.py             # Infix-to-postfix parser (Shunting-Yard) & syntax validator
│   ├── nfa.py                # Thompson's Construction algorithm
│   ├── dfa.py                # Subset Construction (Powerset) algorithm & epsilon-closure
│   ├── minimizer.py          # Hopcroft's DFA Minimization algorithm
│   ├── analyzer.py           # State reduction metrics and ASCII tables
│   ├── simulator.py          # Ground truth string acceptance simulator
│   └── visualizer.py         # DOT, Mermaid, and pipeline orchestration
├── web/
│   ├── index.html            # Studio Web UI Single Page Application
│   ├── styles.css            # Responsive dark/light modern interface
│   └── app.js                # SVG graph renderer and interactive simulator
├── tests/
│   ├── test_parser.py        # Parser unit tests
│   ├── test_nfa.py           # Thompson NFA tests
│   ├── test_dfa.py           # Powerset DFA & Hopcroft tests
│   └── test_pipeline.py      # End-to-end Python re equivalence verification
├── main.py                   # CLI tool
├── server.py                 # Standard library HTTP API server
├── PROJECT_REPORT.md         # Full academic project report & theoretical background
└── README.md                 # Project guide & reference
```

---

## REST API Reference

The server exposes endpoints for integration into third-party tools or web frontends:

- `POST /api/convert`
  - **Body**: `{"regex": "(a|b)*abb"}`
  - **Response**: Full JSON containing NFA, DFA, Minimized DFA, transition matrices, efficiency metrics, and DOT files.
- `POST /api/simulate`
  - **Body**: `{"regex": "(a|b)*abb", "string": "abb"}`
  - **Response**: Simulation verdict (`accepted: true/false`), active states trace, and verification status across automata.
- `GET /api/samples`
  - **Response**: List of predefined textbook benchmark regular expressions.
