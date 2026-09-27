import ast
import math
import operator


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
MAX_EXPRESSION_LENGTH = 500


def _evaluate(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left, right = _evaluate(node.left), _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("Exponent must be between -10 and 10.")
        return _BINARY_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("Use numeric literals and the operators +, -, *, /, %, and ** only.")


def calculator(expression: str) -> dict:
    if len(expression) > MAX_EXPRESSION_LENGTH:
        return {"expression": expression[:MAX_EXPRESSION_LENGTH], "error": "Expression is too long.", "error_type": "ValueError"}
    try:
        tree = ast.parse(expression, mode="eval")
        result = _evaluate(tree.body)
        if isinstance(result, complex):
            raise ValueError("Complex-number results are not supported.")
        if not math.isfinite(result):
            raise ValueError("The result must be a finite number.")
        return {"expression": expression, "result": result}
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError, RecursionError, TypeError) as error:
        return {"expression": expression, "error": str(error), "error_type": type(error).__name__}
