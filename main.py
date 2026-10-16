from flask import Flask, jsonify, request
import ast
import operator
import re

app = Flask(__name__)

keyboard_buffer = ""
output_buffer = []
memory = {}

characters = {}

for i, char in enumerate("abcdefghijklmnopqrstuvwxyz", 1):
    characters[i] = char

for i, char in enumerate("1234567890", 27):
    characters[i] = char

characters.update({
    37: "-",
    38: "=",
    39: ".",
    40: ",",
    41: ";",
    42: "/",
    43: "à",
    44: "à",
    45: "ç",
    46: "è",
    47: "é",
    48: "é",
    49: "î",
    50: "ï",
    51: "û",
    52: "|",
    53: "[",
    54: "]",
    55: "s",
    56: "”",
    91: "!",
    92: "@",
    93: "#",
    94: "$",
    95: "%",
    96: "?",
    97: "&",
    98: "*",
    99: "(",
    100: ")",
    101: "_",
    102: "+",
    103: ".",
    104: "’",
    105: ":",
    106: "~"
})

for i, char in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 64):
    characters[i] = char

character_codes = {}

for code, char in characters.items():
    if char not in character_codes:
        character_codes[char] = code

character_codes["s"] = 19
character_codes["é"] = 47
character_codes["à"] = 43
character_codes["."] = 39


def response(value):
    return jsonify(value=format(value, "08b"))


def read_value():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None

    value = data.get("value")

    if not isinstance(value, str):
        return None

    if len(value) != 8 or any(bit not in "01" for bit in value):
        return None

    return int(value, 2)


def encode_text(text):
    result = []

    for char in text:
        code = character_codes.get(char, 96)
        result.append(code)

    return result


def calculate(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value

    if isinstance(node, ast.Name):
        if node.id in memory:
            return memory[node.id]
        raise ValueError("ERR")

    if isinstance(node, ast.BinOp):
        operations = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv
        }

        operation = operations.get(type(node.op))

        if operation is None:
            raise ValueError("ERR")

        left = calculate(node.left)
        right = calculate(node.right)

        return operation(left, right)

    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.UAdd):
            return calculate(node.operand)

        if isinstance(node.op, ast.USub):
            return -calculate(node.operand)

    raise ValueError("ERR")


def execute_command(command):
    command = command.strip()

    if not command:
        return "ERR"

    assignment = re.fullmatch(
        r"([a-zA-Z][a-zA-Z0-9]*)=(.+)",
        command
    )

    try:
        if assignment:
            name = assignment.group(1)
            expression = assignment.group(2)
            tree = ast.parse(expression, mode="eval")
            result = calculate(tree.body)
            memory[name] = result
            return "OK"

        tree = ast.parse(command, mode="eval")
        result = calculate(tree.body)

        return str(result)

    except Exception:
        return "ERR"


@app.post("/keyboard")
def keyboard():
    global keyboard_buffer

    code = read_value()

    if code is None or code not in characters:
        return response(0)

    if len(keyboard_buffer) < 256:
        keyboard_buffer += characters[code]

    return response(1)


@app.post("/execute")
def execute():
    global keyboard_buffer, output_buffer

    code = read_value()

    if code is None:
        return response(0)

    command = keyboard_buffer
    keyboard_buffer = ""

    result = execute_command(command)
    output_buffer = encode_text(result)

    return response(1)


@app.get("/display")
def display():
    if not output_buffer:
        return response(0)

    code = output_buffer.pop(0)
    return response(code)
