import atexit
import json
import sys
import os
sys.path.append(os.getcwd() + '/libs/')  # Import the libs path.
from traceback import print_exc
import requests
import webbrowser
import time
from controller import (TEAM_CODE,
                        TIME_BETWEEN_MOVES,
                        Controller,)


SERVER_URL = 'http://35.194.64.176'


def main():
    url = "http://35.194.64.176/"
    args = sys.argv[1:]
    if TEAM_CODE == '':
        print('Please enter your team code in the TEAM_CODE variable in controller.py')
        return
    if len(args) == 0:
        print('No team name or test condition provided.')
        return
    elif len(args) == 1 and args[0] == TEAM_CODE:
        print("You cannot provide your own team in the command line argument")
        return
    elif len(args) == 1:
        url += 'challenge/game/' + '/'.join(sorted([TEAM_CODE, args[0]])) + '/watch/'
        manager = GameManager(args[0])
    else:
        print('Incorrect number of arguments provided.')
        return

    # SETUP GAME
    print('Setting Up Game')
    manager.setup_game()

    print('Opening game in default browser')
    webbrowser.open_new_tab(url)
    time.sleep(4)  # Wait four seconds for the browser to open and the game to start.

    manager.post_ready_status()
    manager.start_game_loop()


class GameManager:

    def __init__(self, other_team_code):
        self.team_code = TEAM_CODE
        self.game_url = SERVER_URL + '/challenge/game/'
        teams = sorted([self.team_code, other_team_code])
        self.game_url += '/'.join(teams) + '/'
        self.game_info_url = self.game_url + 'info/'
        self.turn = 0
        self.time_between_moves = max(TIME_BETWEEN_MOVES, 0.3)
        # xx.xx.xx.xx/challenge/game/<aTeamCode>/<bTeamCode>/
        # teams always ordered by alphabetical order.

    def start_game_loop(self):
        student_controller = Controller()
        # get/use game info
        try:
            student_controller.on_game_start(self.maze.maze, self.maze.cols, self.maze.rows)
        except Exception as e:
            print("Exiting game because your code has an error in on_game_start() ...")
            print(e)
            sys.exit(1)
        print("Waiting for other player.")
        started = False
        # In each loop, ping the server to check if it's our turn yet.
        # On approval and receipt of the game info, we can make our move.
        while (True):
            r = self.get_move_permission()  # contains metadata if we can move.
            if self.can_move(r):
                player_coordinates = self.get_player_coords(r)
                bank_coordinates = self.make_items_dict(r)['BANKS']
                # events = self.make_events_dict(r)
                if not started:
                    started = True
                    print("Other player ready.\nGAME STARTED!")
                try:
                    moves = student_controller.on_my_turn(self.maze.maze, player_coordinates, bank_coordinates)
                except Exception as e:
                    print("Your code hit an error in on_my_turn(). Keeping players still... ")
                    print(e)
                    sys.exit(1)
                # Move verification happens on the server side.
                r = self.send_move(moves)
            time.sleep(self.time_between_moves)

    def setup_game(self):
        atexit.register(post_quit_game, self.game_info_url, self.team_code)
        game_data = self.get_game_data()
        self.load_game(game_data)

    def load_game(self, data):
        # LOAD MAZE
        self.maze = Maze(data['cols'], data['rows'])
        self.maze.load_from_array(data['maze'])

        # LOAD TEAM INFO

    def get_player_coords(self, response):
        data = response.json()
        d = {
            'COPS': [coord.encode('utf-8') if coord else None for coord in data['COPS']['players']],
            'ROBBERS': [coord.encode('utf-8') if coord else None for coord in data['ROBBERS']['players']],  # TODO: Limit robbers to cops. Server side.
        }
        return d

    def make_items_dict(self, response):
        data = response.json()
        d = {
            'BANKS': [bank.encode('utf-8') if bank else None for bank in data['banks']],
        }
        return d

    def make_events_dict(self, response):
        if 'events' in response.json():
            return response.json()['events']
        else:
            return {}

    def get_maze(self):
        return self.maze

    def get_game_data(self):
        r = requests.get(self.game_url)
        if r.status_code != 200:
            self.open_error_in_browser(r)
            print(r)
            print("Server error occured. Please check temp_error.html")
            sys.exit("Couldn't retrieve game data.")
        game_data = r.json()
        return game_data

    def send_move(self, moves):
        return self.post(self.game_info_url, 'MOVE', extra={'moves': moves})

    def get_move_permission(self):
        return self.post(self.game_info_url, 'MOVE_PERMISSION', extra={'turn': self.turn})

    def can_move(self, r):
        return r.json()['PERMISSION_TO_MOVE']

    def post_pause_game(self):
        if self.post(self.game_info_url, 'PAUSE'):
            print('Game Paused')

    def post_ready_status(self):
        for i in range(5):
            if (self.post(self.game_info_url, 'READY').status_code == 200):
                print('READY TO PLAY!')
                return True
            else:
                print("Attempt " + i + ": Could not ready the game.")
                time.sleep(1)
        print("Failed to ready game.")
        return False

    def post(self, url, purpose, extra={}):
        data = {
            'CLIENT_TEAM_CODE': TEAM_CODE,
            'REQUEST_PURPOSE': purpose,
        }
        data.update(extra)
        r = requests.post(url, json=data)
        # if purpose != 'MOVE_PERMISSION':
            # print('>>' + str(r))
            # print(r.request.body.encode('utf-8'))
            # print(r.text.encode('utf-8'))
        if r.status_code != 200:
            try:
                error = r.json()['error']
            except ValueError as e:
                self.open_error_in_browser(r)
            error = "EXITING GAME: " + error
            sys.exit(error)
        else:
            return r

    def open_error_in_browser(self, request):
        path = os.path.abspath('logs/temp_error.html')
        url = 'file://' + path
        with open(path, 'w') as f:
            f.write(request.content)
        webbrowser.open(url)


class Maze:

    def __init__(self, cols, rows):
        self.rows = rows
        self.cols = cols
        self.maze = [[Node(col, row) for row in range(rows)] for col in range(cols)]

    def load_from_array(self, node_array):
        # Assign neighbors from dict.
        for col in node_array:
            for node in col:  # for row in col
                if node['up'] is not None:
                    col, row = map(int, node['up'].split(':'))
                    currCol, currRow = map(int, node['coordinates'].split(':'))
                    self.maze[currCol][currRow].set_up(self.maze[col][row])
                if node['down'] is not None:
                    col, row = map(int, node['down'].split(':'))
                    currCol, currRow = map(int, node['coordinates'].split(':'))
                    self.maze[currCol][currRow].set_down(self.maze[col][row])
                if node['left'] is not None:
                    col, row = map(int, node['left'].split(':'))
                    currCol, currRow = map(int, node['coordinates'].split(':'))
                    self.maze[currCol][currRow].set_left(self.maze[col][row])
                if node['right'] is not None:
                    col, row = map(int, node['right'].split(':'))
                    currCol, currRow = map(int, node['coordinates'].split(':'))
                    self.maze[currCol][currRow].set_right(self.maze[col][row])


class Node:

    def __init__(self, col, row):
        self.up = None
        self.down = None
        self.left = None
        self.right = None
        self.col = col
        self.row = row

    def get_up(self):
        return self.up

    def get_down(self):
        return self.down

    def get_left(self):
        return self.left

    def get_right(self):
        return self.right

    def set_right(self, node):
        self.right = node

    def set_left(self, node):
        self.left = node

    def set_down(self, node):
        self.down = node

    def set_up(self, node):
        self.up = node

    def coordinates(self):
        return str(self.col) + ':' + str(self.row)

    def __str__(self):
        return "Node(" + str(self.col) + ":" + str(self.row) + "): ({}{}{}{})".format(
            'U' if self.up else "",
            'D' if self.down else "",
            'L' if self.left else "",
            "R" if self.right else "")

    def __repr__(self):
        return str(self)

def post_quit_game(url, team_code):
    if requests.post(url,
                     json={'CLIENT_TEAM_CODE': team_code, 'REQUEST_PURPOSE': 'QUIT'}
                     ).status_code == 200:
        print("Game quit successfully")


if __name__ == '__main__':
    main()
