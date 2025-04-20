from pyweb import pydom
from scoping.actions import VarValAction
from scoping.core import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph

class TicTacToe:
    def __init__(self):
        self.board = pydom["table#board"]
        self.status = pydom["h2#status"]
        self.console = pydom["script#console"][0]
        self.init_cells()
        self.init_winning_combos()
        self.new_game(...)
        self.scoping_task = None

    def set_status(self, text):
        self.status.html = text

    def init_cells(self):
        self.cells = []
        for i in (0, 1, 2):
            row = []
            for j in (0, 1, 2):
                cell = pydom[f"div#cell{i}{j}"][0]
                assert cell
                row.append(cell)
            self.cells.append(row)

    def init_winning_combos(self):
        self.winning_combos = []
        # winning columns
        for i in (0, 1, 2):
            combo = []
            for j in (0, 1, 2):
                combo.append((i, j))
            self.winning_combos.append(combo)

        # winning rows
        for j in (0, 1, 2):
            combo = []
            for i in (0, 1, 2):
                combo.append((i, j))
            self.winning_combos.append(combo)

        # winning diagonals
        self.winning_combos.append([(0, 0), (1, 1), (2, 2)])
        self.winning_combos.append([(0, 2), (1, 1), (2, 0)])

    def new_game(self, event):
        self.clear_terminal()
        print('=================')
        print('NEW GAME STARTING')
        print()
        for i in (0, 1, 2):
            for j in (0, 1, 2):
                self.set_cell(i, j, "")

        self.current_player = "x"
        self.set_status(f'{self.current_player} playing...')

    def next_turn(self):
        winner = self.check_winner()
        if winner == "tie":
            self.set_status("It's a tie!")
            self.current_player = "" # i.e., game ended
            return
        elif winner is not None:
            self.set_status(f'{winner} wins')
            self.current_player = "" # i.e., game ended
            return

        if self.current_player == "x":
            self.current_player = "o"
        else:
            self.current_player = "x"
        self.set_status(f'{self.current_player} playing...')

    def check_winner(self):
        """
        Check whether the game as any winner.

        Return "x", "o", "tie" or None. None means that the game is still playing.
        """
        # check whether we have a winner
        for combo in self.winning_combos:
            winner = self.get_winner(combo)
            if winner:
                # highlight the winning cells
                for i, j in combo:
                    self.cells[i][j].add_class("win")
                return winner

        # check whether it's a tie
        for i in (0, 1, 2):
            for j in (0, 1, 2):
                if self.get_cell(i, j) == "":
                    # there is at least an empty cell, it's not a tie
                    return None # game still playing
        return "tie"

    def get_winner(self, combo):
        """
        If all the cells at the given points have the same value, return it.
        Else return "".

        Each point is a tuple of (i, j) coordinates.
        Example:
            self.get_winner([(0, 0), (1, 1), (2, 2)])
        """
        assert len(combo) == 3
        values = [self.get_cell(i, j) for i, j in combo]
        if values[0] == values[1] == values[2] and values[0] != "":
            return values[0]
        return ""

    def set_cell(self, i, j, value):
        assert value in ("", "x", "o")
        cell = self.cells[i][j]
        cell.html = value
        if "x" in cell.classes:
            cell.remove_class("x")
        if "o" in cell.classes:
            cell.remove_class("o")
        if "win" in cell.classes:
            cell.remove_class("win")
        if value != "":
            cell.add_class(value)

    def get_cell(self, i, j):
        cell = self.cells[i][j]
        value = cell.html
        assert value in ("", "x", "o")
        return value

    def click(self, event):
        i = int(event.target.getAttribute('data-x'))
        j = int(event.target.getAttribute('data-y'))
        print(f'Cell {i}, {j} clicked: ', end='')
        if self.current_player == "":
            print('game ended, nothing to do')
            return
        #
        value = self.get_cell(i, j)
        if value == "":
            print('cell empty, setting it')
            self.set_cell(i, j, self.current_player)
            self.next_turn()
        else:
            print(f'cell already full, cannot set it')

    def clear_terminal(self):
        self.console._js.terminal.clear()
    
    def toggle_terminal(self, event):
        hidden = self.console.parent._js.getAttribute("hidden")
        if hidden:
            self.console.parent._js.removeAttribute("hidden")
        else:
            self.console.parent._js.setAttribute("hidden", "hidden")
    
    def make_task(
        self,
        domains=FactSet(
            {
                "job": {0, 1},
                "hungry": {0, 1},
                "food": {0, 1},
                "money": {0, 1},
                "serves": {0, 1, 2},
            }
        ),
        actions=[
            VarValAction("a. dance", [("hungry", 0)], [("hungry", 1)], 1),
            VarValAction("d. hunt", [("hungry", 0)], [("food", 1)], 1),
            VarValAction("c. cook", [("food", 1), ("money", 0)], [("serves", 2)], 1),
            VarValAction("b. gather", [("hungry", 1)], [("food", 1)], 1),
            VarValAction("e. hire_chef", [("food", 1), ("money", 1)], [("serves", 2)], 1),
            VarValAction("f. takeout", [("food", 0), ("money", 1)], [("serves", 2)], 1),
            VarValAction("g. get_job", [], [("job", 1)], 1),
            VarValAction("h. work", [("job", 1)], [("money", 1)], 1),
            VarValAction("i. leftovers", [("food", 0)], [("serves", 1)], 1),
        ],
        init=[
            ("job", 1),
            ("hungry", 0),
            ("food", 0),
            ("money", 1),
            ("serves", 0),
        ],
        goal=[
            ("serves", 2),
        ],
    ):
        self.scoping_task = ScopingTask(domains, init, goal, actions)

    def visualize(self):
        self.make_task()
        TaskGraph(self.scoping_task, ScopingOptions(0, 0, 0, 0, 0)).show()

GAME = TicTacToe()
