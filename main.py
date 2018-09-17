#!/usr/bin/env python

import websocket
import json

AUTH_STRING = "player8:1111"

# {
# 	"turns_to_flamout": 1, // jak dlouho žije oheň
# 	"turns_to_replenish_used_bomb": 12, // za jak dlouho se přičte bomba
# 	"turns_to_explode": 10, // za jak dlouho bomba exploduje
# 	"points_per_wall": 1, // kolik je bodů za zničení jedné zdi
# 	"points_per_kill": 10, // kolik je bodů za zabití hráče
# 	"points_per_suicide": -10 // kolik je bodů za zabití sám sebe
# }
PLAYER = 'P'
BOMB = 'B'
FIRE = 'F'
PFIRE = 'f'
UPGRADE_INV = 'n'
UPGRADE_RAD = 'r'
WALL = '#'
BREAKABLE = '.'
SPACE = ' '
DANGERS = {FIRE, PFIRE, BOMB}
UNWALKABLE = {WALL, BOMB, FIRE, BREAKABLE}

game_config = None
mem = {}


# def is_dangerous(c):
#     return c == BOMB or c == FIRE


def get_board(state):
    len_x = len(state['Board'])
    len_y = len(state['Board'][0])
    board = [[None] * len_y] * len_x
    bombs = []
    for x in range(len_x):
        for y in range(len_y):
            board[x][y] = state['Board'][x][y]
            if board[x][y] == BOMB:
                bombs.append((x, y))
    radius = max((p['Radius'] for p in state['Players']))
    for bom in bombs:
        for i in range(1, radius + 1):
            x = bom[0] + i
            y = bom[1]
            if board[x][y] == WALL or board[x][y] == BOMB or board[x][y] == BREAKABLE:
                break
            board[x][y] = PFIRE
        for i in range(1, radius + 1):
            x = bom[0] - i
            y = bom[1]
            if board[x][y] == WALL or board[x][y] == BOMB or board[x][y] == BREAKABLE:
                break
            board[x][y] = PFIRE
        for i in range(1, radius + 1):
            x = bom[0]
            y = bom[1] + i
            if board[x][y] == WALL or board[x][y] == BOMB or board[x][y] == BREAKABLE:
                break
            board[x][y] = PFIRE
        for i in range(1, radius + 1):
            x = bom[0]
            y = bom[1] - i
            if board[x][y] == WALL or board[x][y] == BOMB or board[x][y] == BREAKABLE:
                break
            board[x][y] = PFIRE
    return board


def is_dangerous(board, x, y):
    return board[x][y] in DANGERS


def cant_walk(board, x, y):
    return board[x][y] in UNWALKABLE


def escape_to_safety(state, board):
    curr_x, curr_y = state['X'], state['Y']
    queue = [
        (curr_x + 1, curr_y, 'right'),
        (curr_x - 1, curr_y, 'left'),
        (curr_x, curr_y + 1, 'down'),
        (curr_x, curr_y - 1, 'up'),
    ]
    i = 0
    while i < len(queue):
        sq_x = queue[i][0]
        sq_y = queue[i][1]
        direction = queue[i][2]
        i += 1
        if cant_walk(board, sq_x, sq_y):
            continue
        if not is_dangerous(board, sq_x, sq_y):
            return direction
        queue += [
            (sq_x + 1, sq_y, direction),
            (sq_x - 1, sq_y, direction),
            (sq_x, sq_y + 1, direction),
            (sq_x, sq_y - 1, direction),
        ]
    return 'waiting for death... :/'


def bounty_hunt(state, board):
    curr_x, curr_y = state['X'], state['Y']
    return 'nothing'


# policko_v_pravo = state['Board'][curr_x + 1][curr_y]
def do_move(state):
    curr_x, curr_y = state['X'], state['Y']
    board = get_board(state)
    if is_dangerous(board, curr_x, curr_y):
        # find path to safety
        return escape_to_safety(state, board)
    else:
        # points!
        return bounty_hunt(state, board)


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

    response = do_move(state)
    print(response)
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
        "ws://bomberman.ksp:8003/",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever()
