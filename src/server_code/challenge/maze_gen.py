import random
import json

from challenge.models import Settings


class Node:

    imgs = {
        0x0000: 'none.png',
        0x0001: 'u.png',
        0x0010: 'r.png',
        0x0011: 'ur.png',
        0x0100: 'd.png',
        0x0101: 'ud.png',
        0x0110: 'rd.png',
        0x0111: 'urd.png',
        0x1000: 'l.png',
        0x1001: 'ul.png',
        0x1010: 'rl.png',
        0x1011: 'url.png',
        0x1100: 'dl.png',
        0x1101: 'udl.png',
        0x1110: 'rdl.png',
        0x1111: 'urdl.png'
    }

    def __init__(self, col, row):
        self.left = None
        self.right = None
        self.up = None
        self.down = None
        self.visited = False
        self.img = None
        self.item = None
        self.col = col
        self.row = row

    def ref(self):
        return str(self.col) + ':' + str(self.row)

    def to_dict(self):
        return {
            'coordinates': self.ref(),
            'img': self.img,
            'item': self.item,
            'up': self.up.ref() if self.up else None,
            'right': self.right.ref() if self.right else None,
            'down': self.down.ref() if self.down else None,
            'left': self.left.ref() if self.left else None,
        }


class MazeGen:

    directions = {
        0: 'E',
        1: 'S',
        2: 'W',
        3: 'N',
    }

    def __init__(self, settings, maze=None):
        self.cols = settings.cols
        self.rows = settings.rows
        if maze:
            self.maze = maze
        else:
            self.maze = [[Node(col, row) for row in range(self.rows)] for col in range(self.cols)]
        self.gen_stack = []

    @classmethod
    def load(cls, maze_dict):
        rows = maze_dict['rows']
        cols = maze_dict['cols']
        maze = [[Node(col, row) for row in range(rows)] for col in range(cols)]
        # Assign neighbors from dict.
        for node in maze_dict['maze']:
            if node['up'] is not None:
                col, row = node['up'].split(':')
                node.up = maze[col][row]
            if node['down'] is not None:
                col, row = node['down'].split(':')
                node.up = maze[col][row]
            if node['left'] is not None:
                col, row = node['left'].split(':')
                node.up = maze[col][row]
            if node['right'] is not None:
                col, row = node['right'].split(':')
                node.up = maze[col][row]
        return cls(Settings.get_default(), maze=maze)

    def generate(self, settings):
        # Select two nodes, one at each side of the array.
        # Then we commence a depth first search of the left to the right node.
        # When we run out of unvisited cells to visit, we hit the stack and
        # and start recursing from there.
        col = 0
        row = int(self.rows / 2)
        left_side_node = self.maze[col][row]
        self.dfs(col, row)
        self.labyrinthify(settings.labyrinth_degree)
        self.assign_images()
        self.bank_coordinates = self.place_banks(num=settings.num_banks)
        self.cop_coordinates = self.place_players(int(self.rows * 0.2), num_players=settings.num_cops)
        self.robber_coordinates = self.place_players(self.rows - 1, num_players=settings.num_robbers)

    def dfs(self, col, row):
        while(True):
            curr_node = self.maze[col][row]
            curr_node.visited = True
            # get the next random neighbor
            direction = ""
            neighbors = self.collect_neighbors(col, row)

            if all(n is None for n in neighbors):
                # We've ran out of adjacent options
                # If stack is empty, we're done.
                if (len(self.gen_stack) == 0):
                    break
                # Get something from the stack.
                col, row = self.index_of(self.gen_stack.pop())
                continue
            else:
                self.gen_stack.append(curr_node)
            while (True):
                choice = random.randint(0, 3)
                direction = MazeGen.directions[choice]
                if neighbors[choice]:
                    break

            col, row = self.index_of(neighbors[choice])
            next_node = self.maze[col][row]
            if direction == 'N':
                curr_node.up = next_node
                next_node.down = curr_node
            elif direction == 'S':
                curr_node.down = next_node
                next_node.up = curr_node
            elif direction == 'W':
                curr_node.left = next_node
                next_node.right = curr_node
            else:
                curr_node.right = next_node
                next_node.left = curr_node
            # next_neighbors = self.collect_neighbors(i, j)
            # for n in filter(None, next_neighbors):
            #     self.gen_stack.append(n)

    def collect_neighbors(self, col, row, include_visited=False):
        # TODO: verify
        neighbors = [None] * 4
        if col + 1 < len(self.maze):
            neighbors[0] = self.maze[col+1][row]  # east
            if not include_visited and neighbors[0].visited:
                neighbors[0] = None
        if row + 1 < len(self.maze[0]):
            neighbors[1] = self.maze[col][row+1]  # south
            if not include_visited and neighbors[1].visited:
                neighbors[1] = None
        if col - 1 >= 0:
            neighbors[2] = self.maze[col-1][row]  # west
            if not include_visited and neighbors[2].visited:
                neighbors[2] = None
        if row - 1 >= 0:
            neighbors[3] = self.maze[col][row-1]  # north
            if not include_visited and neighbors[3].visited:
                neighbors[3] = None
        return (neighbors)

    def labyrinthify(self, degree):
        for c in range(int(self.rows*self.cols*degree)):
            col = random.randint(0, self.cols - 1)
            row = random.randint(0, self.rows - 1)
            cross = bool(random.getrandbits(1))  # crossroad (open all) if one
            node = self.maze[col][row]
            neighbors = self.collect_neighbors(col, row, include_visited=True)
            if cross:
                if neighbors[0]:  # E
                    node.right = neighbors[0]
                    neighbors[0].left = node
                if neighbors[1]:  # S
                    node.down = neighbors[1]
                    neighbors[1].up = node
                if neighbors[2]:  # W
                    node.left = neighbors[2]
                    neighbors[2].right = node
                if neighbors[3]:  # N
                    node.up = neighbors[3]
                    neighbors[3].down = node
            else:
                # we add another pathway
                for q in range(4):
                    choice = random.randint(0, 3)
                    if choice == 0 and node.right is None and neighbors[0]:
                        node.right = neighbors[0]
                        neighbors[0].left = node
                        break
                    if choice == 1 and node.down is None and neighbors[1]:
                        node.down = neighbors[1]
                        neighbors[1].up = node
                        break
                    if choice == 2 and node.left is None and neighbors[2]:
                        node.left = neighbors[2]
                        neighbors[2].right = node
                        break
                    if choice == 3 and node.up is None and neighbors[3]:
                        node.up = neighbors[3]
                        neighbors[3].down = node
                        break

    def place_banks(self, num=1, spread=0.4):
        width = int(self.cols * spread) - 1  # How many columns the banks can be spread across
        height = self.rows
        coords = []
        x_start = int((1 - spread) / 2 * self.cols)  # To keep the distribution of banks centered.
        for bank in range(num):
            col = (x_start + random.randint(0, width)) % self.cols
            row = random.randint(0, height) % self.rows
            self.maze[col][row].item = "bank"
            coords += [str(col) + ':' + str(row)]
        return coords

    def place_players(self, col, num_players=2):
        starting_row = int(self.rows/2 - num_players/2)
        player_coordinates = []
        for y in range(num_players):
            player_coordinates += [(str(col) + ":" + str(starting_row + y))]  # col:row
        return player_coordinates

    def index_of(self, node):
        return (node.col, node.row)

    def assign_images(self):
        for col in range(self.cols):
            for row in range(self.rows):
                self.assign_image(col, row)

    def assign_image(self, col, row):
        node = self.maze[col][row]
        hex_gate = 0x0000
        if node.up:
            hex_gate |= 0x0001
        if node.right:
            hex_gate |= 0x0010
        if node.down:
            hex_gate |= 0x0100
        if node.left:
            hex_gate |= 0x1000
        node.img = node.imgs[hex_gate]

    def to_json(self):
        # Creates a json string of the maze.
        return self.to_dict()

    def to_dict(self):
        return {
            'rows': self.rows,
            'cols': self.cols,
            'maze': [[node.to_dict() for node in col] for col in self.maze]
        }

    @staticmethod
    def get_node_from_maze_array(maze, col, row):
        # gets from a flat list only
        return maze[col][row]


def main():
    maze = MazeGen(100, 100)
    maze.generate()
    # Verify complete. All nodes should be visited.
    for i in range(len(maze.maze)):
        for j in range(len(maze.maze[0])):
            if not maze.maze[i][j].visited:
                print('Incomplete!')
                return -1
    print('Complete!')
    maze.to_json()


# if __name__ == "__main__":
#     main()
