
from flask import Flask, request, jsonify, render_template_string
from collections import deque
from threading import Lock

app = Flask(__name__)
lock = Lock()

outgoing = deque()
incoming_text = ""

characters = {
    0: " ",
    1: "a", 2: "b", 3: "c", 4: "d", 5: "e",
    6: "f", 7: "g", 8: "h", 9: "i", 10: "j",
    11: "k", 12: "l", 13: "m", 14: "n", 15: "o",
    16: "p", 17: "q", 18: "r", 19: "s", 20: "t",
    21: "u", 22: "v", 23: "w", 24: "x", 25: "y",
    26: "z",
    27: "1", 28: "2", 29: "3", 30: "4", 31: "5",
    32: "6", 33: "7", 34: "8", 35: "9", 36: "0",
    37: "-", 38: "=", 39: ".", 40: ",", 41: ";",
    42: "/", 43: "à", 44: "à", 45: "ç", 46: "è",
    47: "é", 48: "é", 49: "î", 50: "ï", 51: "û",
    52: "|", 53: "[", 54: "]", 55: "s", 56: "”",
    64: "A", 65: "B", 66: "C", 67: "D", 68: "E",
    69: "F", 70: "G", 71: "H", 72: "I", 73: "J",
    74: "K", 75: "L", 76: "M", 77: "N", 78: "O",
    79: "P", 80: "Q", 81: "R", 82: "S", 83: "T",
    84: "U", 85: "V", 86: "W", 87: "X", 88: "Y",
    89: "Z",
    91: "!", 92: "@", 93: "#", 94: "$", 95: "%",
    96: "?", 97: "&", 98: "*", 99: "(", 100: ")",
    101: "_", 102: "+", 103: ".", 104: "’",
    105: ":", 106: "~"
}

encode = {}

for code, char in characters.items():
    if char not in encode:
        encode[char] = code

encode.update({
    " ": 0,
    "s": 19,
    "à": 43,
    "é": 47,
    ".": 39
})

def binary_response(value, ready=True):
    return jsonify({
        "value": format(value, "08b"),
        "ready": ready
    })

def read_binary():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        data = request.form.to_dict()

    value = data.get("value")

    if not isinstance(value, str):
        return None

    if len(value) != 8 or any(bit not in "01" for bit in value):
        return None

    return int(value, 2)

@app.get("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Binary Chat</title>
<style>
body{font-family:Arial,sans-serif;max-width:700px;margin:40px auto;padding:0 16px;background:#111827;color:#f9fafb}
h1{margin-bottom:8px}
p{color:#cbd5e1}
#chat{height:320px;overflow-y:auto;background:#1f2937;border-radius:10px;padding:14px;white-space:pre-wrap;overflow-wrap:anywhere}
form{display:flex;gap:8px;margin-top:12px}
input{flex:1;min-width:0;padding:12px;border-radius:8px;border:1px solid #475569;background:#1f2937;color:white}
button{padding:12px 18px;border:0;border-radius:8px;background:#2563eb;color:white;cursor:pointer}
#status{font-size:13px}
</style>
</head>
<body>
<h1>Binary Chat</h1>
<p>Messages are encoded using your custom binary table.</p>
<div id="chat"></div>
<form id="form">
<input id="message" autocomplete="off" placeholder="Type a message..." required>
<button type="submit">Send</button>
</form>
<p id="status">Connected to the server.</p>
<script>
const chat = document.getElementById("chat");
const form = document.getElementById("form");
const message = document.getElementById("message");
const statusText = document.getElementById("status");

form.addEventListener("submit", async event => {
    event.preventDefault();
    const text = message.value;
    statusText.textContent = "Sending...";
    try {
        const response = await fetch("/send", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({text})
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Send failed");
        message.value = "";
        statusText.textContent = "Message queued for Build Logic.";
    } catch (error) {
        statusText.textContent = error.message;
    }
});

async function refreshMessages() {
    try {
        const response = await fetch("/messages");
        const result = await response.json();
        chat.textContent = result.text;
        chat.scrollTop = chat.scrollHeight;
    } catch (error) {
        statusText.textContent = "Connection problem.";
    }
}

refreshMessages();
setInterval(refreshMessages, 1000);
</script>
</body>
</html>
""")

@app.post("/send")
def send():
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not isinstance(data.get("text"), str):
        return jsonify(error="Send JSON with a text field."), 400

    text = data["text"]

    if not text:
        return jsonify(error="Message cannot be empty."), 400

    codes = []

    for char in text:
        if char not in encode:
            return jsonify(error="Unsupported character: " + char), 400
        codes.append(encode[char])

    with lock:
        outgoing.extend(codes)

    return jsonify(ok=True, characters=len(codes))

@app.get("/outgoing")
def get_outgoing():
    with lock:
        if not outgoing:
            return binary_response(0, False)
        code = outgoing.popleft()

    return binary_response(code, True)

@app.post("/incoming")
def receive_incoming():
    global incoming_text

    code = read_binary()

    if code is None or code not in characters:
        return binary_response(0, False), 400

    with lock:
        incoming_text += characters[code]

    return binary_response(1, True)

@app.get("/messages")
def get_messages():
    with lock:
        text = "Player: " + incoming_text if incoming_text else ""

    return jsonify(text=text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
