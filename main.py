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
UNWALKABLE = {WALL, BOMB, BREAKABLE}
WALKABLE = {SPACE, UPGRADE_INV, UPGRADE_RAD}

game_config = None
mem = {'counter': 0, 'bomb': False, 'first_move': False}


def get_board(state):
    global mem
    len_x = len(state['Board'])
    len_y = len(state['Board'][0])
    board = [[None for _ in range(len_y)] for _ in range(len_x)]
    bombs = []
    if mem['bomb']:
        bombs.append((state['X'], state['Y']))
    for x in range(len_x):
        for y in range(len_y):
            board[x][y] = state['Board'][x][y]
            if board[x][y] == BOMB:
                bombs.append((x, y))
    radius = max((p['Radius'] for p in state['Players']))
    stop_set = {WALL, BOMB, BREAKABLE}
    for bom in bombs:
        for i in range(1, radius + 1):
            x = bom[0] + i
            y = bom[1]
            if board[x][y] in stop_set:
                break
            board[x][y] = PFIRE
        for i in range(1, radius + 1):
            x = bom[0] - i
            y = bom[1]
            if board[x][y] in stop_set:
                break
            board[x][y] = PFIRE
        for i in range(1, radius + 1):
            x = bom[0]
            y = bom[1] + i
            if board[x][y] in stop_set:
                break
            board[x][y] = PFIRE
        for i in range(1, radius + 1):
            x = bom[0]
            y = bom[1] - i
            if board[x][y] in stop_set:
                break
            board[x][y] = PFIRE
    # for p in board:
    #     print(p)
    return board


def is_dangerous(board, x, y):
    return board[x][y] in DANGERS


def cant_walk(board, x, y):
    return board[x][y] in UNWALKABLE


def possible_choices(board, curr_x, curr_y):
    choices = []
    if board[curr_x + 1][curr_y] in WALKABLE:
        choices.append('right')
    if board[curr_x - 1][curr_y] in WALKABLE:
        choices.append('left')
    if board[curr_x][curr_y + 1] in WALKABLE:
        choices.append('down')
    if board[curr_x][curr_y - 1] in WALKABLE:
        choices.append('up')
    return choices


def escape_to_safety(state, board):
    print('escape')
    curr_x, curr_y = state['X'], state['Y']
    queue = [
        # (x, y, move to do, last direction)
        (curr_x + 1, curr_y, 'right', 'left'),
        (curr_x - 1, curr_y, 'left', 'right'),
        (curr_x, curr_y + 1, 'down', 'up'),
        (curr_x, curr_y - 1, 'up', 'down'),
    ]
    i = 0
    while i < len(queue):
        sq_x = queue[i][0]
        sq_y = queue[i][1]
        move_to_do = queue[i][2]
        direction = queue[i][3]
        i += 1
        if cant_walk(board, sq_x, sq_y):
            continue
        if not is_dangerous(board, sq_x, sq_y):
            # print(queue)
            return move_to_do
        if direction != 'right':
            queue.append((sq_x + 1, sq_y, move_to_do, 'left'))
        if direction != 'left':
            queue.append((sq_x - 1, sq_y, move_to_do, 'right'))
        if direction != 'down':
            queue.append((sq_x, sq_y + 1, move_to_do, 'up'))
        if direction != 'up':
            queue.append((sq_x, sq_y - 1, move_to_do, 'down'))
    return 'waiting for death... :/'


def bounty_hunt(state, board):
    curr_x, curr_y = state['X'], state['Y']
    global mem, game_config
    counter_threshold = game_config['turns_to_explode'] + game_config['turns_to_flamout']
    if mem['counter'] > 4 + counter_threshold \
            and state['Bombs'] > 0:
        mem['bomb'] = True
        mem['counter'] = 0
        return 'bomb'
    else:
        choices = possible_choices(board, curr_x, curr_y)
        return random.choice(choices)


# policko_v_pravo = state['Board'][curr_x + 1][curr_y]


def do_move(state):
    global mem
    board = get_board(state)
    curr_x, curr_y = state['X'], state['Y']
    mem['counter'] += 1
    if not mem['first_move']:
        mem['first_move'] = True
        mem['counter'] = 6
        choices = possible_choices(board, curr_x, curr_y)
        return random.choice(choices)
    if is_dangerous(board, curr_x, curr_y) or mem['bomb']:
        # find path to safety
        if mem['bomb']:
            mem['bomb'] = False
        return escape_to_safety(state, board)
    else:
        # points!
        return bounty_hunt(state, board)


def on_message(ws, message):
    global game_config
    print('==========================')
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
        print("Final score: %s" % state['Points'])
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


if '__main__' == __name__:
    player_n = input('> ')
    ws = websocket.WebSocketApp(
        "ws://192.168.1.100:8002",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=lambda w: w.send("player%s:1111" % player_n)
    )
    ws.run_forever()
