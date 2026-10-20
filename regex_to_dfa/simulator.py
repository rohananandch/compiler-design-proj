"""
Automaton String Simulator Module.

Simulates input strings on NFA, DFA, and Minimized DFA to verify language
equivalence and generate step-by-step execution traces for educational display.
"""

from typing import Dict, List, Set, Tuple, Any
from regex_to_dfa.parser import EPSILON
from regex_to_dfa.nfa import NFA
from regex_to_dfa.dfa import DFA, compute_epsilon_closure
from regex_to_dfa.minimizer import MinimizedDFA


class AutomatonSimulator:
    """Simulates strings on NFA, DFA, and Minimized DFA."""

    @staticmethod
    def simulate_nfa(nfa: NFA, input_string: str) -> Dict[str, Any]:
        """
        Simulates an input string on an NFA using set-of-states tracking with ε-closures.
        Returns acceptance result and step-by-step path trace.
        """
        current_states = compute_epsilon_closure({nfa.start_state.id}, nfa)
        trace = [{
            "step": 0,
            "symbol": "ε-start",
            "active_states": sorted(list(current_states))
        }]

        for idx, char in enumerate(input_string):
            # Move on char
            move_targets = set()
            for s in current_states:
                targets = nfa.get_transitions(s, char)
                move_targets.update(targets)

            # ε-closure on move targets
            current_states = compute_epsilon_closure(move_targets, nfa)
            trace.append({
                "step": idx + 1,
                "symbol": char,
                "active_states": sorted(list(current_states))
            })

            if not current_states:
                break

        accepted = nfa.accept_state.id in current_states
        return {
            "accepted": accepted,
            "final_states": sorted(list(current_states)),
            "trace": trace
        }

    @staticmethod
    def simulate_dfa(dfa: DFA, input_string: str) -> Dict[str, Any]:
        """
        Simulates an input string on a DFA.
        Returns acceptance result and step-by-step path trace.
        """
        curr = dfa.start_state.id
        trace = [{
            "step": 0,
            "symbol": "start",
            "state_id": curr,
            "state_name": f"D{curr}"
        }]

        rejected_early = False
        for idx, char in enumerate(input_string):
            nxt = dfa.get_transition(curr, char)
            if nxt is None:
                trace.append({
                    "step": idx + 1,
                    "symbol": char,
                    "state_id": None,
                    "state_name": "TRAP / SINK (Rejected)"
                })
                rejected_early = True
                break

            curr = nxt
            trace.append({
                "step": idx + 1,
                "symbol": char,
                "state_id": curr,
                "state_name": f"D{curr}"
            })

        final_state_obj = dfa.get_state_by_id(curr) if not rejected_early else None
        accepted = bool(final_state_obj and final_state_obj.is_accept)

        return {
            "accepted": accepted,
            "final_state": curr if not rejected_early else None,
            "trace": trace
        }

    @staticmethod
    def simulate_min_dfa(min_dfa: MinimizedDFA, input_string: str) -> Dict[str, Any]:
        """
        Simulates an input string on a Minimized DFA.
        Returns acceptance result and step-by-step path trace.
        """
        curr = min_dfa.start_state.id if min_dfa.start_state else 0
        trace = [{
            "step": 0,
            "symbol": "start",
            "state_id": curr,
            "state_name": f"M{curr}"
        }]

        rejected_early = False
        for idx, char in enumerate(input_string):
            nxt = min_dfa.get_transition(curr, char)
            if nxt is None:
                trace.append({
                    "step": idx + 1,
                    "symbol": char,
                    "state_id": None,
                    "state_name": "TRAP / SINK (Rejected)"
                })
                rejected_early = True
                break

            curr = nxt
            trace.append({
                "step": idx + 1,
                "symbol": char,
                "state_id": curr,
                "state_name": f"M{curr}"
            })

        final_state_obj = next((s for s in min_dfa.states if s.id == curr), None) if not rejected_early else None
        accepted = bool(final_state_obj and final_state_obj.is_accept)

        return {
            "accepted": accepted,
            "final_state": curr if not rejected_early else None,
            "trace": trace
        }

    @classmethod
    def test_string(cls, input_string: str, nfa: NFA, dfa: DFA, min_dfa: MinimizedDFA) -> Dict[str, Any]:
        """
        Tests a string against all three automata and checks equivalence.
        """
        nfa_res = cls.simulate_nfa(nfa, input_string)
        dfa_res = cls.simulate_dfa(dfa, input_string)
        min_res = cls.simulate_min_dfa(min_dfa, input_string)

        is_equivalent = (nfa_res["accepted"] == dfa_res["accepted"] == min_res["accepted"])

        return {
            "input_string": input_string,
            "accepted": min_res["accepted"],
            "equivalent_across_all": is_equivalent,
            "nfa": nfa_res,
            "dfa": dfa_res,
            "min_dfa": min_res
        }
