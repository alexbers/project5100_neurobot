import time
import os
import re
import json

import numpy as np
from flask import Flask, Response, request, jsonify
from werkzeug.contrib.fixers import ProxyFix

import game
from nnet import NNet
from mcts import MCTS

EFFECTS = [
    "addNb", "removeNb", "setbigbi", "setsmallbi", "setbigbd", "setsmallbd", "addNs", "removeNs", "setbigsi", "setsmallsi", 
    "setbigsd", "setsmallsd", "setbigips", "setsmallips", "thanos", "removeNm"
]

model = NNet(os.path.join("model", "checkpoint_39.pth.tar.next"))
app = Flask(__name__)

def a2str(a):
    if a < 16:
        return "my " + EFFECTS[a]
    elif a < 32:
        return "enemy " + EFFECTS[a-16]
    elif a < 48:
        return "drop " + EFFECTS[a-32]
    elif a == 48:
        return "skip"


def convert_s_to_ap(s, b):
    moves = game.getValidMoves(b, 1)
    ap = [(a2str(i), s[i]) for i in range(len(s)) if moves[i]]
    ap.sort(key=lambda a: a[1], reverse=True)
    return ap


def raw_predict(b):
    global model
    s, v = model.predict(b)
    ap = convert_s_to_ap(s, b)
    return ap, v


def calc_best_move(b, sims=160, cpuct=1.0):
    global model
    print(str(b))

    start = time.time()
    mcts = MCTS(model, {'numMCTSSims': sims, 'cpuct': cpuct})
        
    ap, v = raw_predict(b)

    s = mcts.getActionProb(b, temp=1.0)
    ap2 = convert_s_to_ap(s, b)    
    best_move = np.argmax(s)

    return {
        "best_move": a2str(best_move), 
        "board_value": v, 
        "raw_model_probs": ap, 
        "mcts_probs": ap2, 
        "calc_time": time.time() - start
    }

@app.route("/")
def index():
    ans = "This is a bot server<br><br>"
    ans += "Examples:<br>"
    ans += "/bot?myS=10000&myB=100&myM=10000000&myCooldown=0&myEffectsTimeLeft=0000000000000000&myCardsAvailable=1111100000000000&enemyS=15000&enemyB=100&enemyM=2000000000&enemyCooldown=3&enemyEffectsTimeLeft=0000000000000000"
    return ans

@app.route("/bot")
def bot():
    PARAMS_NEEDED = [
        "myS", "myB", "myM", "myCooldown", "myEffectsTimeLeft", "myCardsAvailable", 
        "enemyS", "enemyB", "enemyM", "enemyCooldown", "enemyEffectsTimeLeft"
    ]

    for param in PARAMS_NEEDED:
        if param not in request.args:
            return jsonify({"error": f"param {param} wasn't found"})

    b = game.getInitBoard()
    b.myS = request.args.get("myS", type=int)
    b.myB = request.args.get("myB", type=int)
    b.myM = request.args.get("myM", type=int)
    b.myCooldown = request.args.get("myCooldown", type=int)

    myEffectsTimeLeft = request.args.get("myEffectsTimeLeft", type=str)
    if not re.fullmatch(r"[0-9a-f]{16}", myEffectsTimeLeft):
        return jsonify({"error": f"param myEffectsTimeLeft is invalid"})
    b.myEffectsTimeLeft = [int(c, 16) for c in myEffectsTimeLeft]
    
    myCardsAvailable = request.args.get("myCardsAvailable", type=str)
    if not re.fullmatch(r"[0-1]{16}", myCardsAvailable):
        return jsonify({"error": f"param myCardsAvailable is invalid"})
    b.myCardsAvailable = [int(c) for c in myCardsAvailable]
    
    b.enemyS = request.args.get("enemyS", type=int)
    b.enemyB = request.args.get("enemyB", type=int)
    b.enemyM = request.args.get("enemyM", type=int)
    b.enemyCooldown = request.args.get("enemyCooldown", type=int)
    
    enemyEffectsTimeLeft = request.args.get("enemyEffectsTimeLeft", type=str)
    if not re.fullmatch(r"[0-9a-f]{16}", enemyEffectsTimeLeft):
        return jsonify({"error": f"param enemyEffectsTimeLeft is invalid"})
    b.enemyEffectsTimeLeft = [int(c, 16) for c in enemyEffectsTimeLeft]

    return jsonify(calc_best_move(b))
    
@app.route("/human")
def human():
    ans = json.loads(bot().data)
    if "error" in ans:
        return ans["error"]


    ret = []
    # ret.append("""<style> h1 p { font-family: monospace; } </style>""")

    ret.append(f"best_move: {ans['best_move']}")
    ret.append(f"board_value: {ans['board_value']:.3f}")
    ret.append(f"calc_time: {ans['calc_time']:.3f}")
    ret.append("raw_model_probs:")
    for move, prob in ans["raw_model_probs"]:
        ret.append(f" {move:<20} {prob:.3f}")
    ret.append("mcts_probs:")
    for move, prob in ans["mcts_probs"]:
        ret.append(f" {move:<20} {prob:.3f}")

    ans = "\n".join(ret)
    return Response(ans, mimetype='text/plain')
    
app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == "__main__":
    app.run()
