from minesweeper import core
from typing import List

class ReplayBoard(core.Board):
    def __init__(self, replay: core.Board, turns):
        super().__init__(replay.rows, replay.cols, replay.mines)
        self._board = replay._board
        self._tiles = replay._tiles
        self._timer = replay._timer
        self._timer1 = replay._timer1
        self._opened = replay._opened
        self._turns = turns
        self._curr_turn = len(turns) - 1

    def tile_open(self, i, j) -> List[core.BoardTile]:
        self._opened +=1
        self._curr_turn += 1
        
        self._tiles[i][j] = self._board[i][j]
        if self._tiles[i][j] == 0:
            return self.__tiles_open_adjacent__(i, j, [self._tiles[i][j]])
        return [self._tiles[i][j]]

    def tile_unopen(self, i, j):
        self._opened -= 1
        self._curr_turn -= 1

        if self._tiles[i][j].number == -2 or self._tiles[i][j].number > 0:
            self._tiles[i][j] = core.BoardTile(core.BoardTile.unopened,i, j)
        else:
            self.__tiles_unopen_adjacent__(i, j)


    def __tiles_unopen_adjacent__(self, row, col):
        for i in [row, row+1, row-1]:
            for j in [col, col+1, col-1]:
                if self.tile_valid(i, j) and self._tiles[i][j].number >= 0 and (row, col) not in self._turns[:self._curr_turn + 1]:
                    self._opened -= 1
                    self._tiles[i][j] = core.BoardTile(core.BoardTile.unopened, i, j)
                    if self._board[i][j].number == 0:
                        self.__tiles_unopen_adjacent__(i, j)


    def game_reset(self) -> core.Board:
        return core.Board(self.rows, self.cols, self.mines)

    def change_turn(self, inc: int):
        if inc < 0 and self._curr_turn >= 0:
            turn = self._turns[self._curr_turn]
            self.tile_unopen(turn[0], turn[1])
        elif inc > 0 and self._curr_turn < len(self._turns) - 1:
            turn = self._turns[self._curr_turn + 1]
            self.tile_open(turn[0], turn[1])

    def first_turn(self):
        for t in self._turns[self._curr_turn::-1]:
            self.tile_unopen(t[0], t[1])

    def last_turn(self):
        for t in self._turns[self._curr_turn + 1:]:
            self.tile_open(t[0], t[1])