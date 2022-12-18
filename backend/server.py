import eventlet

eventlet.monkey_patch()
import errno
import json
import logging
import os
import sys
import dbmanager as db
import reloadedboard, replayboard

from flask import Flask, redirect
from flask_socketio import SocketIO, emit
from logdecorator import log_on_start
from minesweeper import core

logging.basicConfig()
GAME_LOGGER = logging.getLogger("minesweeper")
GAME_LOGGER.setLevel(logging.INFO)


def get_static_folder():
    STATIC_FOLDER_ENV_VAR = "MINESWEEPER_STATIC_FOLDER"
    folder = os.getenv(STATIC_FOLDER_ENV_VAR)

    if folder is None:
        logging.error(
            f"{STATIC_FOLDER_ENV_VAR} variable must be set in the environment."
        )
        sys.exit(errno.EINTR)

    return folder


app = Flask(__name__, static_url_path="", static_folder=get_static_folder())
socketio = SocketIO(app)
GAME_LOGGER.info("Setting up minesweeper board")
account = ""
board = core.Board(rows=16, cols=16, mines=40)


@app.route("/")
def open_page():
    return redirect("index.html")


@socketio.on("board")
@log_on_start(logging.INFO, "Board state requested", logger=GAME_LOGGER)
def get_board():
    if account and (not isinstance(board, reloadedboard.ReloadedBoard) and not isinstance(board, replayboard.ReplayBoard)):
        db.start_game(account, json.dumps(getTileData()), json.dumps(getMineData()), board._timer)
    emit("board", json.dumps(getTileData()), broadcast=True)


@socketio.on("login")
@log_on_start(logging.INFO, "Login attempt", logger=GAME_LOGGER)
def login(username, password):
    global account
    if (db.authenticate(username, password)):
        account = username
        emit("loginsuccess", username, broadcast=True)
    else:
        emit("loginfail")

@socketio.on("logout")
@log_on_start(logging.INFO, "Logging out", logger=GAME_LOGGER)
def logout():
    global account
    account = ""

@socketio.on("register")
@log_on_start(logging.INFO, "Register attempt", logger=GAME_LOGGER)
def register(username, password):
    if (db.register(username, password)):
        emit("registersuccess", broadcast=True)
    else:
        emit("registerfail", broadcast=True)


@socketio.on("open")
@log_on_start(
    logging.INFO,
    "Attempting to open tile at row {row}, column {col}",
    logger=GAME_LOGGER,
)
def open_tile(row, col):
    first_turn = board._opened == 0
    # to ensure DB only stores valid moves
    result = board.tile_open(row, col)
    if first_turn and account:
        db.update_board(account, json.dumps(getMineData()))
    if account and result:
        db.make_move(account, json.dumps(getTileData()))
        db.store_move(account, row, col)
    if board.is_game_finished:
        end_game(True)
    elif board.is_game_over:
        end_game(False)
    else :
        emit("open", json.dumps(getTileData()), broadcast=True)
    

@socketio.on("load")
@log_on_start(logging.INFO, "Loading active game", logger=GAME_LOGGER)
def load(loadedBoard):
    global board
    if loadedBoard is not None:
        board = json.loads(loadedBoard)
    get_board()


@socketio.on("replay")
@log_on_start(logging.INFO, "Loading replay", logger=GAME_LOGGER)
def replay():
    global board
    board = replayboard.ReplayBoard(board, db.get_move_list(account))

@socketio.on("step")
@log_on_start(logging.INFO, "Stepping through replay", logger=GAME_LOGGER)
def replay_step(step):
    if step == "first":
        board.first_turn()
    elif step == "last":
        board.last_turn()
    else:
        board.change_turn(step)
    emit("open", json.dumps(getTileData()), broadcast=True)
    

@socketio.on("resume")
@log_on_start(logging.INFO, "Resuming stored game", logger=GAME_LOGGER)
def resume(username):
    global board, account
    if account != username:
        account = username
    query = db.resume_game(username)
    if query:
        game = query[0]
        board_data = query[1]
        start_time = query[2]
        board = reloadedboard.ReloadedBoard(16, 16, 40, start_time, json.loads(game), json.loads(board_data))
        if board.is_game_finished or board.is_game_over:
            board = replayboard.ReplayBoard(board, db.get_move_list(account))
    else:
        board = core.Board(rows=16, cols=16, mines=40)
    get_board()


@socketio.on("end")
@log_on_start(logging.INFO, "Game has ended", logger=GAME_LOGGER)
def end_game(player_won):
    if account:
        replay()
    if player_won:
        emit("win", json.dumps(getTileData()), broadcast=True)
    else:
        emit("lose", json.dumps(getTileData()), broadcast=True)


@socketio.on("reset")
@log_on_start(logging.INFO, "Resetting game", logger=GAME_LOGGER)
def reset_game():
    global board
    if isinstance(board, reloadedboard.ReloadedBoard) or isinstance(board, replayboard.ReplayBoard):
        board = board.game_reset()
    else:
        board.game_reset()
    if account:
        db.reset_game(account, json.dumps(getTileData()), json.dumps(getMineData()), board._timer)
    emit("board", json.dumps(getTileData()), broadcast=True)


def getTileData():
    tiles = []
    for r in range(board.rows):
        row_tiles = []
        tiles.append(row_tiles)
        for c in range(board.cols):
            row_tiles.append(board._tiles[r][c].type)
    return tiles

#this will be used to store board data to specify mine location
def getMineData():
    tiles = []
    for r in range(board.rows):
        row_tiles = []
        tiles.append(row_tiles)
        for c in range(board.cols):
            row_tiles.append(board._board[r][c].type)
    return tiles


def main():
    socketio.run(app, port=os.getenv("PORT", "8080"))


if __name__ == "__main__":
    main()
    