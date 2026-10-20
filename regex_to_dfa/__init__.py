"""
Regex to Minimized DFA Compiler Module.

Complete pipeline:
Regex -> Postfix (Shunting-Yard) -> NFA (Thompson) -> DFA (Subset Construction) -> Minimized DFA (Hopcroft)
"""

from regex_to_dfa.parser import (
    infix_to_postfix,
    validate_syntax,
    insert_explicit_concatenations,
    extract_alphabet,
    RegexParseError,
    EPSILON
)
from regex_to_dfa.nfa import (
    NFA,
    NFAState,
    build_nfa_from_postfix
)
from regex_to_dfa.dfa import (
    DFA,
    DFAState,
    nfa_to_dfa,
    compute_epsilon_closure,
    compute_move
)
from regex_to_dfa.minimizer import (
    MinimizedDFA,
    MinimizedDFAState,
    minimize_dfa_hopcroft
)
from regex_to_dfa.analyzer import (
    EfficiencyMetrics,
    calculate_metrics
)
from regex_to_dfa.simulator import (
    AutomatonSimulator
)
from regex_to_dfa.visualizer import (
    run_pipeline,
    PipelineResult,
    export_dot_nfa,
    export_dot_dfa,
    export_dot_min_dfa,
    ascii_table_nfa,
    ascii_table_dfa,
    ascii_table_min_dfa
)

__all__ = [
    "infix_to_postfix",
    "validate_syntax",
    "insert_explicit_concatenations",
    "extract_alphabet",
    "RegexParseError",
    "EPSILON",
    "NFA",
    "NFAState",
    "build_nfa_from_postfix",
    "DFA",
    "DFAState",
    "nfa_to_dfa",
    "compute_epsilon_closure",
    "compute_move",
    "MinimizedDFA",
    "MinimizedDFAState",
    "minimize_dfa_hopcroft",
    "EfficiencyMetrics",
    "calculate_metrics",
    "AutomatonSimulator",
    "run_pipeline",
    "PipelineResult",
    "export_dot_nfa",
    "export_dot_dfa",
    "export_dot_min_dfa",
    "ascii_table_nfa",
    "ascii_table_dfa",
    "ascii_table_min_dfa"
]
