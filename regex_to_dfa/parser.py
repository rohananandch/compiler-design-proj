"""
Regex Parser & Infix-to-Postfix Converter Module.

This module provides:
1. Syntax validation for regular expressions.
2. Explicit concatenation operator insertion ('.').
3. Shunting-Yard algorithm (Dijkstra) to convert infix regex to postfix (RPN) notation.
4. Support for literals, epsilon ('ε', 'E', or empty/escaped), concatenation,
   alternation ('|'), Kleene star ('*'), positive closure ('+'), and optional ('?').
"""

from typing import List, Tuple, Set


class RegexParseError(ValueError):
    """Raised when regular expression syntax is invalid."""
    pass


# Special token constants
EPSILON = 'ε'
CONCAT_OP = '.'
UNION_OP = '|'
STAR_OP = '*'
PLUS_OP = '+'
OPTIONAL_OP = '?'
LPAREN = '('
RPAREN = ')'

# Operator precedence
PRECEDENCE = {
    STAR_OP: 3,
    PLUS_OP: 3,
    OPTIONAL_OP: 3,
    CONCAT_OP: 2,
    UNION_OP: 1,
}

UNARY_OPS = {STAR_OP, PLUS_OP, OPTIONAL_OP}
BINARY_OPS = {CONCAT_OP, UNION_OP}


def is_literal(token: str) -> bool:
    """Check if a token is an alphabet literal or epsilon."""
    if token == EPSILON:
        return True
    # Non-operator characters are literals
    return token not in {CONCAT_OP, UNION_OP, STAR_OP, PLUS_OP, OPTIONAL_OP, LPAREN, RPAREN}


def normalize_regex_input(regex_str: str) -> str:
    """
    Normalizes input regex string:
    - Removes raw whitespace (unless escaped).
    - Converts common epsilon representations ('\\e', 'eps', 'EPS') into 'ε'.
    """
    s = regex_str.strip()
    # Replace common representations of epsilon
    s = s.replace("\\e", EPSILON).replace("\\E", EPSILON)
    # Remove unescaped spaces
    cleaned = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            cleaned.append(s[i:i+2])
            i += 2
        elif s[i].isspace():
            i += 1
        else:
            cleaned.append(s[i])
            i += 1
    return "".join(cleaned)


def validate_syntax(regex_str: str) -> None:
    """
    Validates regex syntax before parsing:
    - Checks for empty input.
    - Checks balanced parentheses.
    - Checks invalid placement of operators (e.g., starting with '|', '*', dangling '|', etc.).
    """
    if not regex_str:
        raise RegexParseError("Regular expression cannot be empty.")

    # Check balanced parentheses
    depth = 0
    for idx, ch in enumerate(regex_str):
        if ch == LPAREN:
            depth += 1
        elif ch == RPAREN:
            depth -= 1
            if depth < 0:
                raise RegexParseError(f"Unmatched closing parenthesis ')' at index {idx}.")
    if depth > 0:
        raise RegexParseError(f"Unmatched opening parenthesis '(' (mismatch count: {depth}).")

    # Check leading operators
    first_char = regex_str[0]
    if first_char in {STAR_OP, PLUS_OP, OPTIONAL_OP}:
        raise RegexParseError(f"Unary operator '{first_char}' cannot appear at the start of expression.")
    if first_char in {UNION_OP, CONCAT_OP}:
        raise RegexParseError(f"Binary operator '{first_char}' cannot appear at the start of expression.")

    # Check trailing binary operators
    last_char = regex_str[-1]
    if last_char in {UNION_OP, CONCAT_OP}:
        raise RegexParseError(f"Expression cannot end with binary operator '{last_char}'.")

    # Check consecutive invalid operators
    for i in range(len(regex_str) - 1):
        c1 = regex_str[i]
        c2 = regex_str[i + 1]

        # Trailing operators after '('
        if c1 == LPAREN and c2 in {STAR_OP, PLUS_OP, OPTIONAL_OP, UNION_OP, CONCAT_OP}:
            raise RegexParseError(f"Invalid operator '{c2}' immediately following '(' at index {i+1}.")

        # Empty parentheses ()
        if c1 == LPAREN and c2 == RPAREN:
            raise RegexParseError(f"Empty parentheses '()' found at index {i}.")

        # Consecutive binary operators like '||'
        if c1 == UNION_OP and c2 in {UNION_OP, CONCAT_OP, STAR_OP, PLUS_OP, OPTIONAL_OP, RPAREN}:
            raise RegexParseError(f"Invalid token '{c2}' following union '|' at index {i+1}.")

        if c1 == CONCAT_OP and c2 in {UNION_OP, CONCAT_OP, STAR_OP, PLUS_OP, OPTIONAL_OP, RPAREN}:
            raise RegexParseError(f"Invalid token '{c2}' following concat '.' at index {i+1}.")


def insert_explicit_concatenations(regex_str: str) -> str:
    """
    Inserts explicit concatenation '.' operators into the regex.
    Concatenation is implied between:
    - literal and literal: 'ab' -> 'a.b'
    - literal and '(': 'a(' -> 'a.('
    - ')' and literal: ')a' -> ').a'
    - ')' and '(': ')( ' -> ').('
    - unary op ('*', '+', '?') and literal: 'a*b' -> 'a*.b'
    - unary op ('*', '+', '?') and '(': 'a*(' -> 'a*.('
    """
    if not regex_str:
        return ""

    tokens = []
    i = 0
    # Tokenize taking escapes into account
    while i < len(regex_str):
        if regex_str[i] == '\\' and i + 1 < len(regex_str):
            tokens.append(regex_str[i:i+2])
            i += 2
        else:
            tokens.append(regex_str[i])
            i += 1

    result = []
    for i in range(len(tokens)):
        t1 = tokens[i]
        result.append(t1)

        if i + 1 < len(tokens):
            t2 = tokens[i + 1]

            # Conditions where t1 can precede a concatenation
            can_precede = (
                is_literal(t1) or
                t1 in UNARY_OPS or
                t1 == RPAREN
            )

            # Conditions where t2 can succeed a concatenation
            can_succeed = (
                is_literal(t2) or
                t2 == LPAREN
            )

            # Do not insert if t1 or t2 is already an explicit CONCAT_OP
            if can_precede and can_succeed and t1 != CONCAT_OP and t2 != CONCAT_OP:
                result.append(CONCAT_OP)

    return "".join(result)


def infix_to_postfix(infix_regex: str) -> str:
    """
    Converts infix regular expression to postfix notation (Reverse Polish Notation)
    using Dijkstra's Shunting-Yard algorithm adapted for regex.

    Example:
        '(a|b)*abb' -> 'ab|*a.b.b.'
        'a(b|c)*'   -> 'abc|*.'
    """
    # Step 1: Normalize and Validate
    normalized = normalize_regex_input(infix_regex)
    validate_syntax(normalized)

    # Step 2: Insert explicit concatenation operators
    explicit_infix = insert_explicit_concatenations(normalized)

    # Tokenize (handling escaped characters)
    tokens = []
    i = 0
    while i < len(explicit_infix):
        if explicit_infix[i] == '\\' and i + 1 < len(explicit_infix):
            tokens.append(explicit_infix[i:i+2])
            i += 2
        else:
            tokens.append(explicit_infix[i])
            i += 1

    output: List[str] = []
    operator_stack: List[str] = []

    for token in tokens:
        if is_literal(token):
            output.append(token)
        elif token == LPAREN:
            operator_stack.append(token)
        elif token == RPAREN:
            while operator_stack and operator_stack[-1] != LPAREN:
                output.append(operator_stack.pop())
            if not operator_stack:
                raise RegexParseError("Mismatched parentheses during parsing.")
            operator_stack.pop()  # Discard LPAREN
        elif token in UNARY_OPS:
            # Unary operators (*, +, ?) have highest precedence and associate left-to-right immediately
            output.append(token)
        elif token in BINARY_OPS:
            # Binary operators (. and |)
            token_prec = PRECEDENCE.get(token, 0)
            while operator_stack:
                top = operator_stack[-1]
                if top == LPAREN:
                    break
                top_prec = PRECEDENCE.get(top, 0)
                # Left associative: pop while top_prec >= token_prec
                if top_prec >= token_prec:
                    output.append(operator_stack.pop())
                else:
                    break
            operator_stack.append(token)
        else:
            raise RegexParseError(f"Unexpected token: '{token}'.")

    while operator_stack:
        op = operator_stack.pop()
        if op == LPAREN:
            raise RegexParseError("Mismatched parentheses at end of expression.")
        output.append(op)

    return "".join(output)


def extract_alphabet(regex_str: str) -> List[str]:
    """
    Extracts the alphabet (distinct input symbols, excluding operators and epsilon)
    in sorted deterministic order.
    """
    symbols = set()
    i = 0
    while i < len(regex_str):
        if regex_str[i] == '\\' and i + 1 < len(regex_str):
            tok = regex_str[i+1]
            if tok not in {EPSILON}:
                symbols.add(tok)
            i += 2
        else:
            tok = regex_str[i]
            if is_literal(tok) and tok != EPSILON:
                symbols.add(tok)
            i += 1
    return sorted(list(symbols))
