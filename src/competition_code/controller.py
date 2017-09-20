TEAM_CODE = 'wdxtu'  # My robbers. TODO: clear before distributing.
TIME_BETWEEN_MOVES = 0.5  # seconds. Minimum of 0.3


# DIRECTIONS
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'
STAY = 'stay'


# Helper function
def get_column_row(coordinate):
    col, row = map(int, coordinate.split(':'))
    return (col, row)


class Controller:
    # Game functions
    def on_game_start(self, maze, num_cols, num_rows):
        '''
        This functions is called at the start of the game. It's not very useful.
        Don't feel obliged to use it.
        '''
        self.maze = maze
        print("Rows: ", num_rows)
        print("Columns: ", num_cols)

    def on_my_turn(self, maze, player_coordinates, banks):
        '''
        This function is called every time that it is your turn to move your players.
        Using the location of your players, your opponents (both stored in player_coordinates
        dictionary), and the banks (stored in banks), determine each players next move.

        Params:
            maze: [][] -> Node: A two-dimensional list of Nodes.
                See the spec for the Node class at the bottom of this file.

            player_coordinates: { 'ROBBERS': a list of coordinates, 'COPS': a list of coordinates }
                where a coordinate is a string "col:row", e.g. "21:23"

            banks: [] -> a list of coordinates of banks.
                where a coordinate is a string "col:row", e.g. "21:23"
        Return:
            moves: { 'ROBBERS': [A list of directions or None]}
        '''

        # import pdb; pdb.set_trace()  # Uncomment this line to enabe the debugger.

        robbers = player_coordinates['ROBBERS']
        move_list = [None] * len(robbers)
        for i in range(len(robbers)):
            if robbers[i] is None:
                continue  # we skip players that are no longer in the game.
            col, row = get_column_row(robbers[i])
            player_node = maze[col][row]
            # Take the first available direction.
            if player_node.get_up() is not None:
                move_list[i] = UP
            elif player_node.get_right() is not None:
                move_list[i] = RIGHT
            elif player_node.get_left() is not None:
                move_list[i] = LEFT
            elif player_node.get_down() is not None:
                move_list[i] = DOWN
            else:
                move_list[i] = STAY

        moves = {
            'ROBBERS': move_list,
        }

        return moves


'''
class Node:

    def __init__(self, col, row):
        self.up = None
        self.down = None
        self.left = None
        self.right = None
        self.col = col
        self.row = row

    def get_up(self):
        return self.up  # Node or None if path is blocked.

    def get_down(self):
        return self.down  # Node or None

    def get_left(self):
        return self.left  # Node or None

    def get_right(self):
        return self.right  # Node or None

    def coordinates(self):
        return str(self.col) + ':' + str(self.row)  # "col:row"

    def __str__(self):
        return "Node(" + str(self.col) + ":" + str(self.row) + "): (\{\}\{\}\{\}\{\})".format(
            'U' if self.up else "",
            'D' if self.down else "",
            'L' if self.left else "",
            "R" if self.right else "")
'''
