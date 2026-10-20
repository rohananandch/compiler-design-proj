"""
Visualizer & Export Module.

Generates:
1. Graphviz DOT representations for NFA, DFA, and Minimized DFA.
2. Mermaid diagram syntax for Markdown embedding.
3. ASCII transition tables for terminal display.
4. Comprehensive end-to-end pipeline execution wrapper for CLI and Web API.
"""

import time
from typing import Dict, Any, List, Optional
from regex_to_dfa.parser import infix_to_postfix, extract_alphabet, EPSILON
from regex_to_dfa.nfa import NFA, build_nfa_from_postfix
from regex_to_dfa.dfa import DFA, nfa_to_dfa
from regex_to_dfa.minimizer import MinimizedDFA, minimize_dfa_hopcroft
from regex_to_dfa.analyzer import calculate_metrics, EfficiencyMetrics


def export_dot_nfa(nfa: NFA) -> str:
    """Exports NFA to Graphviz DOT format."""
    lines = [
        "digraph NFA {",
        "  rankdir=LR;",
        '  node [shape=circle, fontname="Courier", style="filled", fillcolor="#f0f4f8", color="#2b6cb0"];',
        '  edge [fontname="Courier", color="#4a5568"];',
        "  __start [shape=none, label=\"\", width=0, height=0];",
        f'  __start -> "{nfa.start_state.id}";',
        f'  "{nfa.accept_state.id}" [shape=doublecircle, fillcolor="#c6f6d5", color="#22543d"];'
    ]

    for (from_id, sym), targets in sorted(nfa.transitions.items()):
        lbl = "ε" if sym == EPSILON else sym
        for to_id in sorted(targets):
            lines.append(f'  "{from_id}" -> "{to_id}" [label="{lbl}"];')

    lines.append("}")
    return "\n".join(lines)


def export_dot_dfa(dfa: DFA) -> str:
    """Exports DFA to Graphviz DOT format."""
    lines = [
        "digraph DFA {",
        "  rankdir=LR;",
        '  node [shape=circle, fontname="Courier", style="filled", fillcolor="#e6fffa", color="#234e52"];',
        '  edge [fontname="Courier", color="#4a5568"];',
        "  __start [shape=none, label=\"\", width=0, height=0];",
        f'  __start -> "{dfa.start_state.id}";'
    ]

    for s in dfa.states:
        shape = "doublecircle" if s.is_accept else "circle"
        fill = "#c6f6d5" if s.is_accept else "#e6fffa"
        color = "#22543d" if s.is_accept else "#234e52"
        subset_str = ",".join(str(x) for x in sorted(list(s.nfa_subset)))
        lines.append(f'  "{s.id}" [label="{s.name}\\n{{{subset_str}}}", shape={shape}, fillcolor="{fill}", color="{color}"];')

    for (from_id, sym), to_id in sorted(dfa.transitions.items()):
        lines.append(f'  "{from_id}" -> "{to_id}" [label="{sym}"];')

    lines.append("}")
    return "\n".join(lines)


def export_dot_min_dfa(min_dfa: MinimizedDFA) -> str:
    """Exports Minimized DFA to Graphviz DOT format."""
    lines = [
        "digraph MinimizedDFA {",
        "  rankdir=LR;",
        '  node [shape=circle, fontname="Courier", style="filled", fillcolor="#feebc8", color="#7b341e"];',
        '  edge [fontname="Courier", color="#4a5568"];',
        "  __start [shape=none, label=\"\", width=0, height=0];",
        f'  __start -> "{min_dfa.start_state.id if min_dfa.start_state else 0}";'
    ]

    for s in min_dfa.states:
        shape = "doublecircle" if s.is_accept else "circle"
        fill = "#c6f6d5" if s.is_accept else "#feebc8"
        color = "#22543d" if s.is_accept else "#7b341e"
        merged_str = ",".join(min_dfa.partition_mapping.get(s.name, []))
        lines.append(f'  "{s.id}" [label="{s.name}\\n[{merged_str}]", shape={shape}, fillcolor="{fill}", color="{color}"];')

    for (from_id, sym), to_id in sorted(min_dfa.transitions.items()):
        lines.append(f'  "{from_id}" -> "{to_id}" [label="{sym}"];')

    lines.append("}")
    return "\n".join(lines)


def ascii_table_nfa(nfa: NFA) -> str:
    """Generates ASCII transition table for NFA."""
    symbols = sorted(list(nfa.alphabet)) + [EPSILON]
    header = f"{'State':<10} | " + " | ".join(f"{('eps' if s == EPSILON else s):<10}" for s in symbols)
    sep = "-" * len(header)
    lines = [sep, f" NFA TRANSITION TABLE (Total States: {len(nfa.states)})", sep, header, sep]

    for s in sorted(nfa.states, key=lambda x: x.id):
        marker = ""
        if s.id == nfa.start_state.id:
            marker += "-> "
        if s.id == nfa.accept_state.id:
            marker += "* "
        state_label = f"{marker}s{s.id}"

        row_entries = []
        for sym in symbols:
            targets = nfa.get_transitions(s.id, sym)
            if targets:
                t_str = "{" + ",".join(f"s{t}" for t in sorted(targets)) + "}"
            else:
                t_str = "-"
            row_entries.append(f"{t_str:<10}")

        lines.append(f"{state_label:<10} | " + " | ".join(row_entries))

    lines.append(sep)
    return "\n".join(lines)


def ascii_table_dfa(dfa: DFA) -> str:
    """Generates ASCII transition table for Subset DFA."""
    symbols = dfa.alphabet
    header = f"{'State (DFA)':<14} | {'NFA Subsets':<24} | " + " | ".join(f"{s:<8}" for s in symbols)
    sep = "-" * len(header)
    lines = [sep, f" SUBSET DFA TRANSITION TABLE (Total States: {len(dfa.states)})", sep, header, sep]

    for s in dfa.states:
        marker = ""
        if s.id == dfa.start_state.id:
            marker += "-> "
        if s.is_accept:
            marker += "* "
        state_label = f"{marker}{s.name}"
        subset_str = "{" + ",".join(str(x) for x in sorted(list(s.nfa_subset))) + "}"

        row_entries = []
        for sym in symbols:
            target = dfa.get_transition(s.id, sym)
            t_str = f"D{target}" if target is not None else "-"
            row_entries.append(f"{t_str:<8}")

        lines.append(f"{state_label:<14} | {subset_str:<24} | " + " | ".join(row_entries))

    lines.append(sep)
    return "\n".join(lines)


def ascii_table_min_dfa(min_dfa: MinimizedDFA) -> str:
    """Generates ASCII transition table for Minimized DFA."""
    symbols = min_dfa.alphabet
    header = f"{'State (Min)':<14} | {'Merged DFA States':<24} | " + " | ".join(f"{s:<8}" for s in symbols)
    sep = "-" * len(header)
    lines = [sep, f" MINIMIZED DFA TRANSITION TABLE (Total States: {len(min_dfa.states)})", sep, header, sep]

    for s in min_dfa.states:
        marker = ""
        if s.is_start:
            marker += "-> "
        if s.is_accept:
            marker += "* "
        state_label = f"{marker}{s.name}"
        merged_str = "{" + ",".join(min_dfa.partition_mapping.get(s.name, [])) + "}"

        row_entries = []
        for sym in symbols:
            target = min_dfa.get_transition(s.id, sym)
            t_str = f"M{target}" if target is not None else "-"
            row_entries.append(f"{t_str:<8}")

        lines.append(f"{state_label:<14} | {merged_str:<24} | " + " | ".join(row_entries))

    lines.append(sep)
    return "\n".join(lines)


class PipelineResult:
    """Encapsulates all results from executing the complete pipeline."""
    def __init__(
        self,
        regex: str,
        postfix: str,
        nfa: NFA,
        dfa: DFA,
        min_dfa: MinimizedDFA,
        metrics: EfficiencyMetrics
    ):
        self.regex = regex
        self.postfix = postfix
        self.nfa = nfa
        self.dfa = dfa
        self.min_dfa = min_dfa
        self.metrics = metrics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regex": self.regex,
            "postfix": self.postfix,
            "alphabet": self.min_dfa.alphabet,
            "nfa": self.nfa.to_dict(),
            "dfa": self.dfa.to_dict(),
            "min_dfa": self.min_dfa.to_dict(),
            "metrics": self.metrics.to_dict(),
            "dot": {
                "nfa": export_dot_nfa(self.nfa),
                "dfa": export_dot_dfa(self.dfa),
                "min_dfa": export_dot_min_dfa(self.min_dfa)
            }
        }


def run_pipeline(regex_str: str) -> PipelineResult:
    """
    Executes the complete 5-stage transformation pipeline:
    1. Regex Parser & Postfix Conversion
    2. Thompson's NFA Construction
    3. Subset Construction DFA
    4. Hopcroft's DFA Minimization
    5. State Reduction & Efficiency Analysis
    """
    # Stage 1: Parse & Postfix
    t0 = time.perf_counter()
    postfix = infix_to_postfix(regex_str)
    t1 = time.perf_counter()
    parse_time_us = (t1 - t0) * 1_000_000

    # Stage 2: NFA Construction
    t0 = time.perf_counter()
    nfa = build_nfa_from_postfix(postfix)
    t1 = time.perf_counter()
    nfa_time_us = (t1 - t0) * 1_000_000

    # Stage 3: DFA Subset Construction
    t0 = time.perf_counter()
    dfa = nfa_to_dfa(nfa)
    t1 = time.perf_counter()
    dfa_time_us = (t1 - t0) * 1_000_000

    # Stage 4: Hopcroft Minimization
    t0 = time.perf_counter()
    min_dfa = minimize_dfa_hopcroft(dfa)
    t1 = time.perf_counter()
    min_time_us = (t1 - t0) * 1_000_000

    # Stage 5: Efficiency Metrics
    metrics = calculate_metrics(
        regex=regex_str,
        postfix=postfix,
        nfa=nfa,
        dfa=dfa,
        min_dfa=min_dfa,
        parse_time_us=parse_time_us,
        nfa_time_us=nfa_time_us,
        dfa_time_us=dfa_time_us,
        minimization_time_us=min_time_us
    )

    return PipelineResult(
        regex=regex_str,
        postfix=postfix,
        nfa=nfa,
        dfa=dfa,
        min_dfa=min_dfa,
        metrics=metrics
    )
