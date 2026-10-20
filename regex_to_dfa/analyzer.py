"""
State Reduction & Efficiency Metrics Module.

Measures, analyzes, and compares state and transition counts across all
transformation stages (NFA -> DFA -> Minimized DFA). Computes reduction
percentages and execution timings.
"""

import time
from dataclasses import dataclass
from typing import Dict, Any
from regex_to_dfa.nfa import NFA
from regex_to_dfa.dfa import DFA
from regex_to_dfa.minimizer import MinimizedDFA


@dataclass
class EfficiencyMetrics:
    """Holds comparative statistics across transformation stages."""
    regex: str
    postfix: str
    alphabet: list

    # State counts
    nfa_states: int
    dfa_states: int
    min_dfa_states: int

    # Transition counts
    nfa_transitions: int
    nfa_epsilon_transitions: int
    dfa_transitions: int
    min_dfa_transitions: int

    # State reductions (%)
    nfa_to_dfa_state_reduction_pct: float
    dfa_to_min_dfa_state_reduction_pct: float
    nfa_to_min_dfa_total_reduction_pct: float

    # Transition reductions (%)
    nfa_to_min_dfa_trans_reduction_pct: float
    dfa_to_min_dfa_trans_reduction_pct: float

    # Timings (microseconds)
    parse_time_us: float
    nfa_time_us: float
    dfa_time_us: float
    minimization_time_us: float
    total_pipeline_time_us: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regex": self.regex,
            "postfix": self.postfix,
            "alphabet": self.alphabet,
            "counts": {
                "nfa": {
                    "states": self.nfa_states,
                    "transitions": self.nfa_transitions,
                    "epsilon_transitions": self.nfa_epsilon_transitions
                },
                "dfa": {
                    "states": self.dfa_states,
                    "transitions": self.dfa_transitions
                },
                "min_dfa": {
                    "states": self.min_dfa_states,
                    "transitions": self.min_dfa_transitions
                }
            },
            "reductions": {
                "nfa_to_min_dfa_state_pct": round(self.nfa_to_min_dfa_total_reduction_pct, 2),
                "dfa_to_min_dfa_state_pct": round(self.dfa_to_min_dfa_state_reduction_pct, 2),
                "nfa_to_dfa_state_pct": round(self.nfa_to_dfa_state_reduction_pct, 2),
                "nfa_to_min_dfa_trans_pct": round(self.nfa_to_min_dfa_trans_reduction_pct, 2),
                "dfa_to_min_dfa_trans_pct": round(self.dfa_to_min_dfa_trans_reduction_pct, 2),
            },
            "timings_us": {
                "parse": round(self.parse_time_us, 2),
                "nfa": round(self.nfa_time_us, 2),
                "dfa": round(self.dfa_time_us, 2),
                "minimization": round(self.minimization_time_us, 2),
                "total": round(self.total_pipeline_time_us, 2)
            }
        }

    def generate_ascii_table(self) -> str:
        """Produces a clean ASCII comparison table for CLI output."""
        lines = []
        lines.append("=" * 72)
        lines.append("              STATE REDUCTION & EFFICIENCY REPORT")
        lines.append("=" * 72)
        lines.append(f" Input Regex    : {self.regex}")
        lines.append(f" Postfix Form   : {self.postfix}")
        lines.append(f" Input Alphabet : {', '.join(self.alphabet)}")
        lines.append("-" * 72)
        lines.append(f"{'Machine Stage':<22} | {'States':<10} | {'Transitions':<14} | {'Notes':<18}")
        lines.append("-" * 72)
        lines.append(f"{'Thompson NFA':<22} | {self.nfa_states:<10} | {self.nfa_transitions:<14} | {self.nfa_epsilon_transitions} eps-moves")
        lines.append(f"{'Subset DFA':<22} | {self.dfa_states:<10} | {self.dfa_transitions:<14} | Deterministic")
        lines.append(f"{'Hopcroft Min DFA':<22} | {self.min_dfa_states:<10} | {self.min_dfa_transitions:<14} | Fully Minimal")
        lines.append("=" * 72)
        lines.append("                     OPTIMIZATION METRICS")
        lines.append("-" * 72)
        lines.append(f" State Reduction (NFA -> Min DFA)   : {self.nfa_to_min_dfa_total_reduction_pct:.2f}%")
        lines.append(f" State Reduction (DFA -> Min DFA)   : {self.dfa_to_min_dfa_state_reduction_pct:.2f}%")
        lines.append(f" Transition Reduction (NFA -> Min)  : {self.nfa_to_min_dfa_trans_reduction_pct:.2f}%")
        lines.append(f" Total Pipeline Execution Time      : {self.total_pipeline_time_us:.1f} us ({self.total_pipeline_time_us / 1000:.3f} ms)")
        lines.append("=" * 72)
        return "\n".join(lines)


def calculate_metrics(
    regex: str,
    postfix: str,
    nfa: NFA,
    dfa: DFA,
    min_dfa: MinimizedDFA,
    parse_time_us: float,
    nfa_time_us: float,
    dfa_time_us: float,
    minimization_time_us: float
) -> EfficiencyMetrics:
    """Calculates all state reduction metrics and ratios."""
    nfa_states = len(nfa.states)
    dfa_states = len(dfa.states)
    min_states = len(min_dfa.states)

    nfa_trans = nfa.count_transitions()
    nfa_eps = nfa.count_epsilon_transitions()
    dfa_trans = dfa.count_transitions()
    min_trans = min_dfa.count_transitions()

    # Reductions
    nfa_to_dfa_pct = ((nfa_states - dfa_states) / nfa_states * 100) if nfa_states else 0.0
    dfa_to_min_pct = ((dfa_states - min_states) / dfa_states * 100) if dfa_states else 0.0
    nfa_to_min_pct = ((nfa_states - min_states) / nfa_states * 100) if nfa_states else 0.0

    nfa_to_min_trans_pct = ((nfa_trans - min_trans) / nfa_trans * 100) if nfa_trans else 0.0
    dfa_to_min_trans_pct = ((dfa_trans - min_trans) / dfa_trans * 100) if dfa_trans else 0.0

    total_time = parse_time_us + nfa_time_us + dfa_time_us + minimization_time_us

    return EfficiencyMetrics(
        regex=regex,
        postfix=postfix,
        alphabet=min_dfa.alphabet,
        nfa_states=nfa_states,
        dfa_states=dfa_states,
        min_dfa_states=min_states,
        nfa_transitions=nfa_trans,
        nfa_epsilon_transitions=nfa_eps,
        dfa_transitions=dfa_trans,
        min_dfa_transitions=min_trans,
        nfa_to_dfa_state_reduction_pct=nfa_to_dfa_pct,
        dfa_to_min_dfa_state_reduction_pct=dfa_to_min_pct,
        nfa_to_min_dfa_total_reduction_pct=nfa_to_min_pct,
        nfa_to_min_dfa_trans_reduction_pct=nfa_to_min_trans_pct,
        dfa_to_min_dfa_trans_reduction_pct=dfa_to_min_trans_pct,
        parse_time_us=parse_time_us,
        nfa_time_us=nfa_time_us,
        dfa_time_us=dfa_time_us,
        minimization_time_us=minimization_time_us,
        total_pipeline_time_us=total_time
    )
