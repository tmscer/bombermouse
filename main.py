#!/usr/bin/env python

import websocket
import json
import random

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
mem = {'counter': 0, 'bomb': False}


def get_board(state):
    global mem
    len_x = len(state['Board'])
    len_y = len(state['Board'][0])
    board = [[None for _ in range(len_y)] for _ in range(len_x)]
    if not mem['bomb']:
        bombs = []
    else:
        bombs = [(state['X'], state['Y'])]
        mem['bomb'] = False
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
    # for p in board:
    #     print(p)
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
        (curr_x, curr_y + 1, 'up'),
        (curr_x, curr_y - 1, 'down'),
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
            print(queue)
            return direction
        if direction != 'left':
            queue.append((sq_x + 1, sq_y, direction))
        if direction != 'right':
            queue.append((sq_x - 1, sq_y, direction))
        if direction != 'down':
            queue.append((sq_x, sq_y + 1, direction))
        if direction != 'up':
            queue.append((sq_x, sq_y - 1, direction))
    return 'waiting for death... :/'


def bounty_hunt(state, board):
    curr_x, curr_y = state['X'], state['Y']
    global mem
    if mem['counter'] > 9:
        mem['bomb'] = True
        mem['counter'] = 0
        return 'bomb'
    choices = []
    sett = {SPACE, UPGRADE_INV, UPGRADE_RAD}
    if board[curr_x + 1][curr_y] in sett:
        choices.append('right')
    if board[curr_x - 1][curr_y] in sett:
        choices.append('left')
    if board[curr_x][curr_y + 1] in sett:
        choices.append('up')
    if board[curr_x][curr_y - 1] in sett:
        choices.append('down')
    return random.choices(choices)


j = 0


# policko_v_pravo = state['Board'][curr_x + 1][curr_y]


def do_move(state):
    global mem
    mem['counter'] += 1
    # TODO: REMOVE
    if mem['counter'] == 0:
        return 'down'
    elif mem['counter'] == 1:
        return 'bomb'
    elif mem['counter'] == 2:
        return 'left'
    curr_x, curr_y = state['X'], state['Y']
    board = get_board(state)
    print(curr_x, curr_y, board[curr_x][curr_y])
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
    ws.send("player9:abc")


if '__main__' == __name__:
    ws = websocket.WebSocketApp(
        "ws://bomberman.ksp:8000",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever()
