from minesweeper import core
from typing import List

#should only be used on stored accounts loading their games
class ReloadedBoard(core.Board):
    def __init__(self, rows: int, cols: int, mines: int, start: float, loadedBoard: List[List[str]], boardData: List[List[str]]):
        self.loadedBoard = loadedBoard
        self.boardData = boardData
        self.__opened = 0
        super().__init__(rows, cols, mines)
        self._opened = self.__opened
        self._timer = start
        if "x" in self.loadedBoard:
            self._is_game_over = True
        if "t" not in self.loadedBoard:
            self._is_game_finished = True

    #no longer creates random mine locations
    def __init__board__(self) -> List[List[core.BoardTile]]:
        rowf = (
            lambda i, j: core.BoardTile.mine
            if self.boardData[i][j] == "x"
            else self.boardData[i][j]
        )
        return [
            [core.BoardTile(rowf(i,j), i, j) for j in range(self.cols)]
            for i in range(self.rows)
        ]

    #if the tile was opened, set is as its number(or mine), otherwise
    #set as unopened
    def __init__tiles__(self) -> List[List[core.BoardTile]]:
        def rowf(i,j):
            if self.loadedBoard[i][j] == "t":
                return core.BoardTile.unopened
            else:
                self.__opened+= 1
                return self.loadedBoard[i][j]
        return [
            [core.BoardTile(rowf(i,j), i, j) for j in range(self.cols)]
            for i in range(self.rows)
        ]

    def game_reset(self) -> core.Board:
        return core.Board(self.rows, self.cols, self.mines)
