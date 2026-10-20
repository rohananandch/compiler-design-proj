"""
DFA Minimization Module using Hopcroft's Algorithm.

Minimizes a Deterministic Finite Automaton (DFA) by partitioning states into
equivalence classes and merging indistinguishable states.
"""

from typing import Dict, List, Set, Tuple, FrozenSet, Optional
from regex_to_dfa.dfa import DFA, DFAState


class MinimizedDFAState:
    """Represents a state in the minimized DFA, grouping original DFA states."""
    def __init__(self, id: int, name: str, original_states: List[int], is_accept: bool = False, is_start: bool = False):
        self.id = id
        self.name = name
        self.original_states = sorted(original_states)
        self.is_accept = is_accept
        self.is_start = is_start

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, MinimizedDFAState):
            return self.id == other.id
        return False


class MinimizedDFA:
    """
    Represents the minimized DFA resulting from Hopcroft's algorithm.
    """
    def __init__(self, alphabet: List[str]):
        self.alphabet: List[str] = sorted(list(alphabet))
        self.states: List[MinimizedDFAState] = []
        self.start_state: Optional[MinimizedDFAState] = None
        # transitions: (state_id, symbol) -> target_state_id
        self.transitions: Dict[Tuple[int, str], int] = {}
        # Mapping from partition representation to state
        self.partition_mapping: Dict[str, List[int]] = {}

    @property
    def accept_states(self) -> List[MinimizedDFAState]:
        return [s for s in self.states if s.is_accept]

    def add_state(self, state: MinimizedDFAState) -> None:
        self.states.append(state)
        if state.is_start:
            self.start_state = state

    def add_transition(self, from_id: int, symbol: str, to_id: int) -> None:
        self.transitions[(from_id, symbol)] = to_id

    def get_transition(self, from_id: int, symbol: str) -> Optional[int]:
        return self.transitions.get((from_id, symbol), None)

    def count_transitions(self) -> int:
        return len(self.transitions)

    def to_dict(self) -> dict:
        """Serializes Minimized DFA to dictionary for API and visualization."""
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
                "original_states": s.original_states,
                "is_accept": s.is_accept,
                "is_start": s.is_start
            })

        return {
            "type": "MinimizedDFA",
            "start_state": self.start_state.id if self.start_state else 0,
            "accept_states": [s.id for s in self.accept_states],
            "states": states_info,
            "alphabet": self.alphabet,
            "transitions": transitions_list,
            "total_states": len(self.states),
            "total_transitions": self.count_transitions(),
            "partition_mapping": self.partition_mapping
        }


def eliminate_unreachable_states(dfa: DFA) -> Set[int]:
    """Finds all states reachable from the start state."""
    reachable = {dfa.start_state.id}
    queue = [dfa.start_state.id]

    while queue:
        curr = queue.pop(0)
        for sym in dfa.alphabet:
            target = dfa.get_transition(curr, sym)
            if target is not None and target not in reachable:
                reachable.add(target)
                queue.append(target)

    return reachable


def minimize_dfa_hopcroft(dfa: DFA) -> MinimizedDFA:
    """
    Minimizes a DFA using Hopcroft's partition refinement algorithm.
    Time complexity: O(|Σ| * n * log n) where n is the number of states.
    """
    # Step 1: Filter reachable states
    reachable_ids = eliminate_unreachable_states(dfa)
    all_states = [s for s in dfa.states if s.id in reachable_ids]

    if not all_states:
        # Trivial empty DFA
        min_dfa = MinimizedDFA(alphabet=dfa.alphabet)
        return min_dfa

    # Step 2: Initial Partition P = { F, Q \ F }
    F = frozenset(s.id for s in all_states if s.is_accept)
    non_F = frozenset(s.id for s in all_states if not s.is_accept)

    P: Set[FrozenSet[int]] = set()
    if F:
        P.add(F)
    if non_F:
        P.add(non_F)

    # Worklist W initialized to P
    W: Set[FrozenSet[int]] = set(P)

    # Inverted transition table for fast lookup:
    # inv_transitions[sym][target_state] = set of source_states
    inv_transitions: Dict[str, Dict[int, Set[int]]] = {sym: {} for sym in dfa.alphabet}
    for (src, sym), dst in dfa.transitions.items():
        if src in reachable_ids and dst in reachable_ids:
            if dst not in inv_transitions[sym]:
                inv_transitions[sym][dst] = set()
            inv_transitions[sym][dst].add(src)

    # Step 3: Hopcroft's Main Loop
    while W:
        A = W.pop()

        for sym in dfa.alphabet:
            # X = set of states that transition on sym into A
            X = set()
            for dst in A:
                if dst in inv_transitions[sym]:
                    X.update(inv_transitions[sym][dst])

            if not X:
                continue

            X_frozen = frozenset(X)

            # Check each partition block Y in P
            new_P = set()
            for Y in P:
                Y1 = Y.intersection(X_frozen)
                Y2 = Y.difference(X_frozen)

                if Y1 and Y2:
                    # Y is split into Y1 and Y2
                    new_P.add(Y1)
                    new_P.add(Y2)

                    if Y in W:
                        W.remove(Y)
                        W.add(Y1)
                        W.add(Y2)
                    else:
                        # Add the smaller block to W for O(n log n) efficiency
                        if len(Y1) <= len(Y2):
                            W.add(Y1)
                        else:
                            W.add(Y2)
                else:
                    new_P.add(Y)

            P = new_P

    # Step 4: Reconstruct the Minimized DFA from Partition P
    min_dfa = MinimizedDFA(alphabet=dfa.alphabet)

    # Sort partitions to ensure deterministic state naming
    # Ensure partition containing original start state comes first (ID 0)
    start_id = dfa.start_state.id
    sorted_partitions: List[FrozenSet[int]] = sorted(
        list(P),
        key=lambda block: (0 if start_id in block else 1, min(block))
    )

    # Mapping from original state ID to new minimized state ID
    state_to_partition_id: Dict[int, int] = {}
    partition_states: List[MinimizedDFAState] = []

    for idx, block in enumerate(sorted_partitions):
        is_acc = any(dfa.get_state_by_id(sid).is_accept for sid in block if dfa.get_state_by_id(sid))
        is_strt = (start_id in block)
        state_name = f"M{idx}"
        orig_names = [f"D{sid}" for sid in sorted(list(block))]

        min_state = MinimizedDFAState(
            id=idx,
            name=state_name,
            original_states=list(block),
            is_accept=is_acc,
            is_start=is_strt
        )
        min_dfa.add_state(min_state)
        min_dfa.partition_mapping[state_name] = orig_names

        for sid in block:
            state_to_partition_id[sid] = idx

    # Step 5: Add transitions for Minimized DFA
    # For each partition block, take any representative state
    for idx, block in enumerate(sorted_partitions):
        rep = next(iter(block))
        for sym in dfa.alphabet:
            target = dfa.get_transition(rep, sym)
            if target is not None and target in state_to_partition_id:
                target_min_id = state_to_partition_id[target]
                min_dfa.add_transition(idx, sym, target_min_id)

    return min_dfa
