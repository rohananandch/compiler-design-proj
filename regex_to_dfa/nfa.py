"""
Thompson's Construction (NFA Construction) Module with Geometric Layout.

Converts a postfix regular expression into an equivalent Non-deterministic
Finite Automaton (NFA) using Thompson's Construction algorithm.

Maintains canonical geometric shapes matching compiler textbooks and diagrams:
1. Union / Alternation (a|b): Diamond / parallel tracks (upper & lower branches).
2. Kleene Star (a*): Forward ε-line, high top loopback arc, and low bottom bypass arc.
3. Concatenation (ab): Linear sequence with direct state merging (Dragon Book standard)
   or explicit ε-transition.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional, Any
from regex_to_dfa.parser import (
    EPSILON, CONCAT_OP, UNION_OP, STAR_OP, PLUS_OP, OPTIONAL_OP,
    is_literal
)


@dataclass
class NFAState:
    """Represents a state in the NFA."""
    id: int
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = f"s{self.id}"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, NFAState):
            return self.id == other.id
        return False


class NFAStateFactory:
    """Generates sequential state IDs."""
    def __init__(self):
        self._current_id = 0

    def new_state(self) -> NFAState:
        state = NFAState(id=self._current_id)
        self._current_id += 1
        return state

    def reset(self):
        self._current_id = 0


class NFA:
    """
    Non-deterministic Finite Automaton (NFA).
    Defined by 5-tuple (Q, Σ, δ, q0, F):
    - states: Set of states Q
    - alphabet: Set of input symbols Σ (excluding ε)
    - transitions: Dict mapping (state_id, symbol) -> Set of target state_ids
    - start_state: Start state q0
    - accept_state: Single accept state
    - positions: Geometric (x, y) coordinates for visualization
    - edge_routes: Semantic routing for each edge ('straight', 'diagonal', 'loopback_top', 'bypass_bottom')
    - construction_steps: Step-by-step history snapshots of Thompson construction
    """

    def __init__(self, start_state: NFAState, accept_state: NFAState):
        self.start_state: NFAState = start_state
        self.accept_state: NFAState = accept_state
        self.states: Set[NFAState] = {start_state, accept_state}
        self.alphabet: Set[str] = set()
        self.transitions: Dict[Tuple[int, str], Set[int]] = {}
        self.positions: Dict[int, Tuple[float, float]] = {}
        self.edge_routes: Dict[Tuple[int, int, str], str] = {}
        self.construction_steps: List[Dict[str, Any]] = []

    @property
    def accept_states(self) -> Set[NFAState]:
        return {self.accept_state}

    def add_state(self, state: NFAState) -> None:
        self.states.add(state)

    def add_transition(self, from_state: NFAState, symbol: str, to_state: NFAState, route: str = "straight") -> None:
        self.states.add(from_state)
        self.states.add(to_state)
        if symbol != EPSILON:
            self.alphabet.add(symbol)
        key = (from_state.id, symbol)
        if key not in self.transitions:
            self.transitions[key] = set()
        self.transitions[key].add(to_state.id)
        self.edge_routes[(from_state.id, to_state.id, symbol)] = route

    def get_transitions(self, state_id: int, symbol: str) -> Set[int]:
        return self.transitions.get((state_id, symbol), set())

    def get_all_transitions_for_state(self, state_id: int) -> Dict[str, Set[int]]:
        res: Dict[str, Set[int]] = {}
        for (sid, sym), targets in self.transitions.items():
            if sid == state_id:
                res[sym] = targets
        return res

    def count_transitions(self) -> int:
        return sum(len(targets) for targets in self.transitions.values())

    def count_epsilon_transitions(self) -> int:
        return sum(len(targets) for (sid, sym), targets in self.transitions.items() if sym == EPSILON)

    def to_dict(self) -> dict:
        """Serializes NFA with positions, edge routes, and construction steps."""
        transitions_list = []
        for (sid, sym), targets in sorted(self.transitions.items(), key=lambda x: (x[0][0], x[0][1])):
            for t in sorted(targets):
                route = self.edge_routes.get((sid, t, sym), "straight")
                transitions_list.append({
                    "from": sid,
                    "to": t,
                    "symbol": sym,
                    "route": route
                })

        # Format positions
        pos_dict = {}
        for sid, pos in self.positions.items():
            pos_dict[str(sid)] = {"x": round(pos[0], 1), "y": round(pos[1], 1)}

        return {
            "type": "NFA",
            "start_state": self.start_state.id,
            "accept_states": [self.accept_state.id],
            "states": sorted([s.id for s in self.states]),
            "alphabet": sorted(list(self.alphabet)),
            "transitions": transitions_list,
            "positions": pos_dict,
            "total_states": len(self.states),
            "total_transitions": self.count_transitions(),
            "epsilon_transitions": self.count_epsilon_transitions(),
            "construction_steps": self.construction_steps
        }


class LayoutFragment:
    """
    Encapsulates an NFA fragment together with bounding box dimensions,
    relative coordinates, and sub-expression info for geometric composition.
    """
    def __init__(
        self,
        start_id: int,
        accept_id: int,
        states: Set[int],
        transitions: Dict[Tuple[int, str], Set[int]],
        positions: Dict[int, Tuple[float, float]],
        edge_routes: Dict[Tuple[int, int, str], str],
        width: float,
        height_top: float,
        height_bot: float,
        sub_expr: str
    ):
        self.start_id = start_id
        self.accept_id = accept_id
        self.states = set(states)
        self.transitions = {k: set(v) for k, v in transitions.items()}
        self.positions = dict(positions)
        self.edge_routes = dict(edge_routes)
        self.width = width
        self.height_top = height_top
        self.height_bot = height_bot
        self.sub_expr = sub_expr

    def to_nfa(self) -> NFA:
        """Converts fragment to an NFA object."""
        s_start = NFAState(id=self.start_id)
        s_accept = NFAState(id=self.accept_id)
        nfa = NFA(start_state=s_start, accept_state=s_accept)

        for sid in self.states:
            nfa.add_state(NFAState(id=sid))

        for (src, sym), dsts in self.transitions.items():
            for dst in dsts:
                route = self.edge_routes.get((src, dst, sym), "straight")
                nfa.add_transition(NFAState(id=src), sym, NFAState(id=dst), route=route)

        nfa.positions = dict(self.positions)
        nfa.edge_routes = dict(self.edge_routes)
        return nfa


def thompson_literal(symbol: str, factory: Optional[NFAStateFactory] = None) -> NFA:
    """Wrapper function returning base NFA for a literal."""
    return create_literal_fragment(symbol).to_nfa()


def create_literal_fragment(symbol: str) -> LayoutFragment:
    """
    Base literal fragment: (0) --symbol--> (1)
    """
    dx = 110.0
    return LayoutFragment(
        start_id=0,
        accept_id=1,
        states={0, 1},
        transitions={(0, symbol): {1}},
        positions={0: (0.0, 0.0), 1: (dx, 0.0)},
        edge_routes={(0, 1, symbol): "straight"},
        width=dx,
        height_top=35.0,
        height_bot=35.0,
        sub_expr=symbol
    )


def create_union_fragment(fA: LayoutFragment, fB: LayoutFragment) -> LayoutFragment:
    """
    Union / Alternation (A | B):
    Creates the classic Diamond / Hexagon shape:
    - New start state 0
    - Upper branch A shifted to y = -delta_y/2 (states 1 .. nA)
    - Lower branch B shifted to y = +delta_y/2 (states nA+1 .. nA+nB)
    - New accept state (nA + nB + 1)
    - Diagonals connecting start to branches, and branches to accept.
    """
    nA = len(fA.states)
    nB = len(fB.states)
    start_id = 0
    accept_id = nA + nB + 1
    states = set(range(accept_id + 1))

    delta_y = max(fA.height_bot + fB.height_top + 45.0, 110.0)
    yA = -delta_y / 2.0
    yB = delta_y / 2.0
    w_max = max(fA.width, fB.width)
    x_branch = 85.0

    positions: Dict[int, Tuple[float, float]] = {
        start_id: (0.0, 0.0),
        accept_id: (x_branch + w_max + 85.0, 0.0)
    }

    # Shift Fragment A to upper branch (IDs: 1 .. nA)
    for sid, (x, y) in fA.positions.items():
        positions[sid + 1] = (x + x_branch + (w_max - fA.width) / 2.0, y + yA)

    # Shift Fragment B to lower branch (IDs: nA+1 .. nA+nB)
    for sid, (x, y) in fB.positions.items():
        positions[sid + 1 + nA] = (x + x_branch + (w_max - fB.width) / 2.0, y + yB)

    transitions: Dict[Tuple[int, str], Set[int]] = {}
    edge_routes: Dict[Tuple[int, int, str], str] = {}

    # Transitions from start to upper & lower branches
    transitions[(start_id, EPSILON)] = {fA.start_id + 1, fB.start_id + 1 + nA}
    edge_routes[(start_id, fA.start_id + 1, EPSILON)] = "diagonal"
    edge_routes[(start_id, fB.start_id + 1 + nA, EPSILON)] = "diagonal"

    # Copy Fragment A transitions
    for (src, sym), dsts in fA.transitions.items():
        transitions[(src + 1, sym)] = {d + 1 for d in dsts}
    for (src, dst, sym), route in fA.edge_routes.items():
        edge_routes[(src + 1, dst + 1, sym)] = route

    # Copy Fragment B transitions
    for (src, sym), dsts in fB.transitions.items():
        transitions[(src + 1 + nA, sym)] = {d + 1 + nA for d in dsts}
    for (src, dst, sym), route in fB.edge_routes.items():
        edge_routes[(src + 1 + nA, dst + 1 + nA, sym)] = route

    # Transitions from branches to accept
    k_accA = (fA.accept_id + 1, EPSILON)
    transitions[k_accA] = transitions.get(k_accA, set()) | {accept_id}
    edge_routes[(fA.accept_id + 1, accept_id, EPSILON)] = "diagonal"

    k_accB = (fB.accept_id + 1 + nA, EPSILON)
    transitions[k_accB] = transitions.get(k_accB, set()) | {accept_id}
    edge_routes[(fB.accept_id + 1 + nA, accept_id, EPSILON)] = "diagonal"

    width = x_branch + w_max + 85.0
    h_top = abs(yA) + fA.height_top
    h_bot = yB + fB.height_bot
    expr = f"({fA.sub_expr}|{fB.sub_expr})"

    return LayoutFragment(start_id, accept_id, states, transitions, positions, edge_routes, width, h_top, h_bot, expr)


def create_star_fragment(f: LayoutFragment) -> LayoutFragment:
    """
    Kleene Star (A*):
    - New start state 0
    - Inner fragment shifted horizontally by x_in = 85.0 (IDs: 1 .. n)
    - New accept state (n + 1)
    - Straight ε from 0 to inner start (1)
    - Straight ε from inner accept (n) to star accept (n+1)
    - High top loopback arc from inner accept (n) back to inner start (1)
    - Low bottom bypass arc from start (0) forward to star accept (n+1)
    """
    n = len(f.states)
    start_id = 0
    accept_id = n + 1
    states = set(range(accept_id + 1))

    x_in = 85.0
    positions: Dict[int, Tuple[float, float]] = {
        start_id: (0.0, 0.0),
        accept_id: (x_in + f.width + 85.0, 0.0)
    }

    for sid, (x, y) in f.positions.items():
        positions[sid + 1] = (x + x_in, y)

    transitions: Dict[Tuple[int, str], Set[int]] = {}
    edge_routes: Dict[Tuple[int, int, str], str] = {}

    # Start -> inner.start & Start -> accept (bypass)
    transitions[(start_id, EPSILON)] = {f.start_id + 1, accept_id}
    edge_routes[(start_id, f.start_id + 1, EPSILON)] = "straight"
    edge_routes[(start_id, accept_id, EPSILON)] = "bypass_bottom"

    # Copy inner fragment transitions
    for (src, sym), dsts in f.transitions.items():
        transitions[(src + 1, sym)] = {d + 1 for d in dsts}
    for (src, dst, sym), route in f.edge_routes.items():
        edge_routes[(src + 1, dst + 1, sym)] = route

    # Inner.accept -> accept (exit) & Inner.accept -> Inner.start (loopback)
    k_acc = (f.accept_id + 1, EPSILON)
    transitions[k_acc] = transitions.get(k_acc, set()) | {accept_id, f.start_id + 1}
    edge_routes[(f.accept_id + 1, accept_id, EPSILON)] = "straight"
    edge_routes[(f.accept_id + 1, f.start_id + 1, EPSILON)] = "loopback_top"

    width = x_in + f.width + 85.0
    h_top = f.height_top + 55.0
    h_bot = f.height_bot + 55.0
    expr = f"({f.sub_expr})*"

    return LayoutFragment(start_id, accept_id, states, transitions, positions, edge_routes, width, h_top, h_bot, expr)


def create_concat_fragment(fA: LayoutFragment, fB: LayoutFragment, merge: bool = True) -> LayoutFragment:
    """
    Concatenation (A . B):
    In Dragon Book / Image 2 style: merges fA.accept with fB.start.
    fB is shifted horizontally by fA.width.
    """
    if merge:
        shift_id = len(fA.states) - 1
        shift_x = fA.width

        states = set(fA.states)
        positions = dict(fA.positions)
        transitions = {k: set(v) for k, v in fA.transitions.items()}
        edge_routes = dict(fA.edge_routes)

        for sid in fB.states:
            if sid == fB.start_id:
                continue
            new_sid = sid + shift_id
            states.add(new_sid)
            bx, by = fB.positions[sid]
            positions[new_sid] = (bx + shift_x, by)

        for (src, sym), dsts in fB.transitions.items():
            new_src = fA.accept_id if src == fB.start_id else (src + shift_id)
            new_dsts = {(fA.accept_id if d == fB.start_id else (d + shift_id)) for d in dsts}
            k = (new_src, sym)
            transitions[k] = transitions.get(k, set()) | new_dsts

        for (src, dst, sym), route in fB.edge_routes.items():
            new_src = fA.accept_id if src == fB.start_id else (src + shift_id)
            new_dst = fA.accept_id if dst == fB.start_id else (dst + shift_id)
            edge_routes[(new_src, new_dst, sym)] = route

        accept_id = fB.accept_id + shift_id
        width = fA.width + fB.width
        h_top = max(fA.height_top, fB.height_top)
        h_bot = max(fA.height_bot, fB.height_bot)
        expr = f"{fA.sub_expr}{fB.sub_expr}"

        return LayoutFragment(fA.start_id, accept_id, states, transitions, positions, edge_routes, width, h_top, h_bot, expr)

    else:
        # Non-merged concat: connects with an ε-transition
        dx = 80.0
        shift_id = len(fA.states)
        shift_x = fA.width + dx

        states = set(fA.states)
        positions = dict(fA.positions)
        transitions = {k: set(v) for k, v in fA.transitions.items()}
        edge_routes = dict(fA.edge_routes)

        for sid in fB.states:
            new_sid = sid + shift_id
            states.add(new_sid)
            bx, by = fB.positions[sid]
            positions[new_sid] = (bx + shift_x, by)

        for (src, sym), dsts in fB.transitions.items():
            k = (src + shift_id, sym)
            transitions[k] = {d + shift_id for d in dsts}

        for (src, dst, sym), route in fB.edge_routes.items():
            edge_routes[(src + shift_id, dst + shift_id, sym)] = route

        # ε transition between fA.accept and fB.start
        transitions[(fA.accept_id, EPSILON)] = {fB.start_id + shift_id}
        edge_routes[(fA.accept_id, fB.start_id + shift_id, EPSILON)] = "straight"

        accept_id = fB.accept_id + shift_id
        width = shift_x + fB.width
        h_top = max(fA.height_top, fB.height_top)
        h_bot = max(fA.height_bot, fB.height_bot)
        expr = f"{fA.sub_expr}.{fB.sub_expr}"

        return LayoutFragment(fA.start_id, accept_id, states, transitions, positions, edge_routes, width, h_top, h_bot, expr)


def build_nfa_from_postfix(postfix_regex: str, merge_concat: bool = True) -> NFA:
    """
    Constructs an NFA with canonical geometric layout from a postfix regex.
    Captures step-by-step construction history matching textbook derivations.
    """
    stack: List[LayoutFragment] = []
    construction_steps: List[Dict[str, Any]] = []
    step_counter = 1

    tokens = []
    i = 0
    while i < len(postfix_regex):
        if postfix_regex[i] == '\\' and i + 1 < len(postfix_regex):
            tokens.append(postfix_regex[i:i+2])
            i += 2
        else:
            tokens.append(postfix_regex[i])
            i += 1

    for token in tokens:
        if is_literal(token):
            sym = token[1] if token.startswith('\\') else token
            frag = create_literal_fragment(sym)
            stack.append(frag)

        elif token == CONCAT_OP:
            if len(stack) < 2:
                raise ValueError(f"Insufficient operands for concat '{CONCAT_OP}'")
            f2 = stack.pop()
            f1 = stack.pop()
            merged_frag = create_concat_fragment(f1, f2, merge=merge_concat)
            stack.append(merged_frag)

            # Record Construction Step
            step_nfa = merged_frag.to_nfa()
            construction_steps.append({
                "step_number": step_counter,
                "title": f"Step-{step_counter} Concatenate to form {merged_frag.sub_expr}",
                "sub_regex": merged_frag.sub_expr,
                "nfa": step_nfa.to_dict()
            })
            step_counter += 1

        elif token == UNION_OP:
            if len(stack) < 2:
                raise ValueError(f"Insufficient operands for union '{UNION_OP}'")
            f2 = stack.pop()
            f1 = stack.pop()
            union_frag = create_union_fragment(f1, f2)
            stack.append(union_frag)

            # Record Construction Step (e.g., Step-1 First we create ε-NFA for (a/b))
            step_nfa = union_frag.to_nfa()
            construction_steps.append({
                "step_number": step_counter,
                "title": f"Step-{step_counter} Create ε-NFA for {union_frag.sub_expr}",
                "sub_regex": union_frag.sub_expr,
                "nfa": step_nfa.to_dict()
            })
            step_counter += 1

        elif token == STAR_OP:
            if not stack:
                raise ValueError(f"Insufficient operands for star '{STAR_OP}'")
            f = stack.pop()
            star_frag = create_star_fragment(f)
            stack.append(star_frag)

            # Record Construction Step (e.g., Step-2 Then create ε-NFA for (a/b)*)
            step_nfa = star_frag.to_nfa()
            construction_steps.append({
                "step_number": step_counter,
                "title": f"Step-{step_counter} Apply Kleene Star for {star_frag.sub_expr}",
                "sub_regex": star_frag.sub_expr,
                "nfa": step_nfa.to_dict()
            })
            step_counter += 1

        elif token in {PLUS_OP, OPTIONAL_OP}:
            # Handle + and ? using standard Thompson expansions
            if not stack:
                raise ValueError(f"Insufficient operands for '{token}'")
            f = stack.pop()
            star_frag = create_star_fragment(f)
            stack.append(star_frag)
            step_nfa = star_frag.to_nfa()
            construction_steps.append({
                "step_number": step_counter,
                "title": f"Step-{step_counter} Apply Operator for {star_frag.sub_expr}",
                "sub_regex": star_frag.sub_expr,
                "nfa": step_nfa.to_dict()
            })
            step_counter += 1

        else:
            raise ValueError(f"Unknown postfix token: {token}")

    if len(stack) != 1:
        raise ValueError(f"Invalid postfix expression; stack ended with {len(stack)} items.")

    final_fragment = stack[0]
    final_nfa = final_fragment.to_nfa()
    final_nfa.construction_steps = construction_steps
    return final_nfa
