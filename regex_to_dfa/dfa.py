"""
Subset Construction (Powerset Construction) Module.

Converts a Non-deterministic Finite Automaton (NFA) into an equivalent
Deterministic Finite Automaton (DFA) using the Subset Construction algorithm.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, FrozenSet, Optional
from regex_to_dfa.parser import EPSILON
from regex_to_dfa.nfa import NFA


@dataclass
class DFAState:
    """Represents a state in the DFA."""
    id: int
    name: str
    nfa_subset: FrozenSet[int]
    is_accept: bool = False

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, DFAState):
            return self.id == other.id
        return False


class DFA:
    """
    Deterministic Finite Automaton (DFA).
    Defined by 5-tuple (Q, Σ, δ, q0, F):
    - states: Set of DFAState objects
    - alphabet: Set of input symbols Σ (sorted list)
    - transitions: Dict mapping (state_id, symbol) -> target_state_id
    - start_state: Start DFAState
    - accept_states: Set of accepting DFAState objects
    """

    def __init__(self, start_state: DFAState, alphabet: List[str]):
        self.start_state: DFAState = start_state
        self.states: List[DFAState] = [start_state]
        self.alphabet: List[str] = sorted(list(alphabet))
        # transitions: (state_id, symbol) -> target_state_id
        self.transitions: Dict[Tuple[int, str], int] = {}

    @property
    def accept_states(self) -> List[DFAState]:
        return [s for s in self.states if s.is_accept]

    def add_state(self, state: DFAState) -> None:
        if state not in self.states:
            self.states.append(state)

    def add_transition(self, from_id: int, symbol: str, to_id: int) -> None:
        self.transitions[(from_id, symbol)] = to_id

    def get_transition(self, from_id: int, symbol: str) -> Optional[int]:
        return self.transitions.get((from_id, symbol), None)

    def get_state_by_id(self, state_id: int) -> Optional[DFAState]:
        for s in self.states:
            if s.id == state_id:
                return s
        return None

    def count_transitions(self) -> int:
        return len(self.transitions)

    def to_dict(self) -> dict:
        """Serializes DFA to dictionary for API and visualization."""
        transitions_list = []
        for (sid, sym), target in sorted(self.transitions.items(), key=lambda x: (x[0][0], x[0][1])):
            transitions_list.append({
                "from": sid,
                "to": target,
                "symbol": sym
            })

        states_info = []
        for s in self.states:
            states_info.append({
                "id": s.id,
                "name": s.name,
                "nfa_subset": sorted(list(s.nfa_subset)),
                "is_accept": s.is_accept,
                "is_start": (s.id == self.start_state.id)
            })

        return {
            "type": "DFA",
            "start_state": self.start_state.id,
            "accept_states": [s.id for s in self.accept_states],
            "states": states_info,
            "alphabet": self.alphabet,
            "transitions": transitions_list,
            "total_states": len(self.states),
            "total_transitions": self.count_transitions()
        }


def compute_epsilon_closure(states: Set[int], nfa: NFA) -> FrozenSet[int]:
    """
    Computes ε-closure for a set of NFA states.
    ε-closure(S) is the set of all NFA states reachable from S taking zero or more ε-transitions.
    """
    closure = set(states)
    stack = list(states)

    while stack:
        curr = stack.pop()
        # Find ε-transitions from curr
        targets = nfa.get_transitions(curr, EPSILON)
        for t in targets:
            if t not in closure:
                closure.add(t)
                stack.append(t)

    return frozenset(closure)


def compute_move(states: FrozenSet[int], symbol: str, nfa: NFA) -> Set[int]:
    """
    Computes move(T, a): the set of NFA states to which there is a transition
    on symbol 'a' from any state in T.
    """
    move_targets = set()
    for s in states:
        targets = nfa.get_transitions(s, symbol)
        move_targets.update(targets)
    return move_targets


def nfa_to_dfa(nfa: NFA) -> DFA:
    """
    Converts an NFA to an equivalent DFA using the Subset Construction algorithm.
    """
    alphabet = sorted(list(nfa.alphabet))
    nfa_accept_id = nfa.accept_state.id

    # Compute initial DFA state: ε-closure({nfa.start_state})
    initial_subset = compute_epsilon_closure({nfa.start_state.id}, nfa)

    subset_to_dfa: Dict[FrozenSet[int], DFAState] = {}
    queue = deque()

    start_dfa_state = DFAState(
        id=0,
        name="D0",
        nfa_subset=initial_subset,
        is_accept=(nfa_accept_id in initial_subset)
    )

    subset_to_dfa[initial_subset] = start_dfa_state
    queue.append(initial_subset)

    dfa = DFA(start_state=start_dfa_state, alphabet=alphabet)
    current_state_counter = 1

    while queue:
        current_subset = queue.popleft()
        current_dfa_state = subset_to_dfa[current_subset]

        for symbol in alphabet:
            # Step 1: move(current_subset, symbol)
            move_res = compute_move(current_subset, symbol, nfa)
            if not move_res:
                continue

            # Step 2: ε-closure(move_res)
            target_subset = compute_epsilon_closure(move_res, nfa)
            if not target_subset:
                continue

            # Step 3: Check if this subset was already discovered
            if target_subset not in subset_to_dfa:
                is_acc = (nfa_accept_id in target_subset)
                new_state = DFAState(
                    id=current_state_counter,
                    name=f"D{current_state_counter}",
                    nfa_subset=target_subset,
                    is_accept=is_acc
                )
                current_state_counter += 1
                subset_to_dfa[target_subset] = new_state
                dfa.add_state(new_state)
                queue.append(target_subset)

            target_dfa_state = subset_to_dfa[target_subset]
            dfa.add_transition(current_dfa_state.id, symbol, target_dfa_state.id)

    return dfa
