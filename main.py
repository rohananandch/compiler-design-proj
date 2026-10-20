"""
Command-Line Interface (CLI) for Regex-to-Minimized-DFA Compiler Tool.

Usage:
    python main.py "<regex>" [options]
    python main.py --interactive
    python main.py --serve

Examples:
    python main.py "(a|b)*abb"
    python main.py "(a|b)*abb" --simulate "abb" "ab" "bba" "aabb"
    python main.py "a(b|c)*" --export-dot
"""

import sys
import os
import argparse
from typing import List

# Ensure package directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from regex_to_dfa.visualizer import (
    run_pipeline,
    ascii_table_nfa,
    ascii_table_dfa,
    ascii_table_min_dfa,
    export_dot_nfa,
    export_dot_dfa,
    export_dot_min_dfa
)
from regex_to_dfa.simulator import AutomatonSimulator
from regex_to_dfa.parser import RegexParseError


def print_banner():
    banner = """
========================================================================
   COMPILER DESIGN: REGEX TO MINIMIZED DFA TRANSFORMATION PIPELINE
   [Regex Parser] -> [Thompson NFA] -> [Subset DFA] -> [Hopcroft Min DFA]
========================================================================
"""
    print(banner)


def run_cli(regex_str: str, test_strings: List[str] = None, export_dot: bool = False, show_tables: bool = True):
    print_banner()
    print(f" Processing Regular Expression: '{regex_str}' ...\n")

    try:
        result = run_pipeline(regex_str)
    except RegexParseError as e:
        print(f"[Syntax Error] Invalid regular expression: {e}")
        return
    except Exception as e:
        print(f"[Error] Pipeline execution failed: {e}")
        return

    # Print State Reduction & Efficiency Report
    print(result.metrics.generate_ascii_table())
    print()

    # Print Transition Tables
    if show_tables:
        print(ascii_table_nfa(result.nfa))
        print()
        print(ascii_table_dfa(result.dfa))
        print()
        print(ascii_table_min_dfa(result.min_dfa))
        print()

    # Simulate test strings if requested
    if test_strings:
        print("=" * 72)
        print("                   STRING SIMULATION RESULTS")
        print("=" * 72)
        print(f"{'Input String':<16} | {'Accepted?':<12} | {'NFA == DFA == MinDFA':<22} | {'Status':<12}")
        print("-" * 72)
        for s in test_strings:
            display_s = f'"{s}"' if s != "" else '"" (empty)'
            sim_res = AutomatonSimulator.test_string(s, result.nfa, result.dfa, result.min_dfa)
            acc_str = "ACCEPTED" if sim_res["accepted"] else "REJECTED"
            equiv_str = "Verified Match" if sim_res["equivalent_across_all"] else "MISMATCH!"
            status_flag = "[OK]" if sim_res["equivalent_across_all"] else "[FAIL]"
            print(f"{display_s:<16} | {acc_str:<12} | {equiv_str:<22} | {status_flag:<12}")
        print("=" * 72)
        print()

    # Export DOT files if requested
    if export_dot:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_graphs")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "nfa.dot"), "w", encoding="utf-8") as f:
            f.write(export_dot_nfa(result.nfa))
        with open(os.path.join(out_dir, "dfa.dot"), "w", encoding="utf-8") as f:
            f.write(export_dot_dfa(result.dfa))
        with open(os.path.join(out_dir, "min_dfa.dot"), "w", encoding="utf-8") as f:
            f.write(export_dot_min_dfa(result.min_dfa))
        print(f"[Export] Graphviz DOT files generated in: {out_dir}")


def interactive_mode():
    print_banner()
    print(" Interactive Mode: Type regular expressions to analyze.")
    print(" Special commands: 'exit' to quit, 'samples' to see benchmark regexes.\n")

    samples = [
        ("(a|b)*abb", "Classic token pattern: ends with 'abb'"),
        ("(a|b)*a(a|b)", "Pattern where second-to-last symbol is 'a'"),
        ("a(b|c)*", "Identifier prefix with alternatives"),
        ("(0|1)*00(0|1)*", "Binary strings containing '00'"),
        ("(a*b*)*", "Nested Kleene star closure"),
        ("(a|eps)b*", "Optional prefix"),
    ]

    while True:
        try:
            line = input("\nEnter Regex (or 'exit' / 'samples') > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not line:
            continue
        if line.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            break
        if line.lower() == "samples":
            print("\nBenchmark Regular Expressions:")
            for idx, (rgx, desc) in enumerate(samples, 1):
                print(f"  {idx}. {rgx:<18} -> {desc}")
            continue

        test_str_input = input("Enter test strings separated by commas (optional, press Enter to skip): ").strip()
        test_strings = [s.strip() for s in test_str_input.split(",")] if test_str_input else None

        run_cli(line, test_strings=test_strings)


def main():
    parser = argparse.ArgumentParser(
        description="Regex to Minimized DFA Compiler Pipeline: Thompson NFA -> Powerset DFA -> Hopcroft Minimization"
    )
    parser.add_argument("regex", nargs="?", help="Regular expression to convert")
    parser.add_argument("--simulate", "-s", nargs="*", help="Strings to simulate and test on the automaton")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive REPL mode")
    parser.add_argument("--export-dot", "-d", action="store_true", help="Export Graphviz DOT graph files")
    parser.add_argument("--serve", action="store_true", help="Start the interactive web visualizer server")
    parser.add_argument("--port", type=int, default=8000, help="Port for the web server (default: 8000)")

    args = parser.parse_args()

    if args.serve:
        from server import start_server
        start_server(port=args.port)
    elif args.interactive or not args.regex:
        interactive_mode()
    else:
        run_cli(args.regex, test_strings=args.simulate, export_dot=args.export_dot)


if __name__ == "__main__":
    main()
