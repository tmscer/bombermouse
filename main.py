#!/usr/bin/env python

import websocket
import json


AUTH_STRING = "player7:1111"

# {
# 	"turns_to_flamout": 1, // jak dlouho žije oheň
# 	"turns_to_replenish_used_bomb": 12, // za jak dlouho se přičte bomba
# 	"turns_to_explode": 10, // za jak dlouho bomba exploduje
# 	"points_per_wall": 1, // kolik je bodů za zničení jedné zdi
# 	"points_per_kill": 10, // kolik je bodů za zabití hráče
# 	"points_per_suicide": -10 // kolik je bodů za zabití sám sebe
# }
game_config = None
mem = {}


def do_move(state):
    # Current position
    curr_x, curr_y = (state['X'], state['Y'])
    # toto je políčko na pravo od nás
    policko_v_pravo = state['Board'][curr_x + 1][curr_y]
    # ws.send("up")
    # ws.send("down")
    # ws.send("right")
    # ws.send("left")
    # ws.send("bomb")
    return 'up'


def on_message(ws, message):
    global game_config
    state = json.loads(message)
    if 'points_per_wall' in state:
        # první zpráva obsahuje konfiguraci, ne stav hry
        game_config = state
        print("Game config: ")
        print(game_config)
        ws.send('greetings')
        return

    print("Game state: ")
    print(state)

    if not state['Alive']:
        print("We died")
        ws.close()
        return

    print("hi")

    response = do_move(state)
    ws.send(response)
    return


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    ws.send(AUTH_STRING)


if '__main__' == __name__:
    ws = websocket.WebSocketApp(
        "ws://bomberman.ksp:8002/",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever()
