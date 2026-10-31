from flask import Flask
app = Flask(__name__)
reset={"value":"00000000"}

message_o={"value":"00000000"}
message_i={"value":"00000000"}

@app.route("/dev_o", methods=["POST"]) #this in device i
def dev_o(): 
    global message_o, message_i, reset
    message_o=request.json
    return {"value":"00000000"}

@app.route("/dev_i", methods=["POST"]) #this in device o
def dev_i(): 
    global message_o, message_i, reset
    message_i=request.json
    return {"value":"00000000"}

@app.route("/dev_otoi", methods=["GET"]) #this in device i
def dev_otoi(): 
    global message_o, message_i, reset
    if message_o != {"value":"00000000"}:
        temp_data=message_o
        message_o=reset.copy()
        return temp_data
    else:
        return {"value":"00000000"}


@app.route("/dev_itoo", methods=["GET"]) #this in device o
def dev_itoo(): 
    global message_o, message_i, reset
    if message_i != {"value":"00000000"}:
        temp_data_b=message_i
        message_i=reset.copy()
        return temp_data_b
    else:
        return {"value":"00000000"}
        

