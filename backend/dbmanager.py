import sqlalchemy
import hashlib
import time

from sqlalchemy import create_engine, Column, Integer, String, Float, update, delete, asc
from sqlalchemy.orm import Session, relationship, declarative_base
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import JSON, VARCHAR
from sqlalchemy.sql.expression import select


Base = declarative_base()
class Player(Base):
    __tablename__ = "player"

    player_id = Column(VARCHAR(length=16), primary_key=True, nullable=False, unique=True, autoincrement=True)
    password = Column(VARCHAR(length=128), nullable=False)
    games_won = Column(Integer, default=0)
    games_lost = Column(Integer, default=0)

    active_game = relationship("ActiveGame", back_populates="player", uselist=False)

    def __repr__(self):
        return f"Player(player_id={self.player_id!r}, games_won={self.games_won!r}, games_lost={self.games_lost!r})"

class ActiveGame(Base):
    __tablename__ = "active_game"

    game_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    player_id = Column(VARCHAR(length=16), ForeignKey(Player.player_id), nullable=False)
    game_state = Column(JSON)
    board_data = Column(JSON)
    start_time  = Column(Float, nullable=False)

    player = relationship("Player", back_populates="active_game")
    move = relationship("Move", cascade="all,delete", back_populates="active_game")
    def __repr__(self):
        return f"Game=(game_id={self.game_id!r}, player_id={self.player_id!r}, game_state={self.game_state!r}, board_data={self.board_data!r}, start_time={self.start_time!r})"

class Move(Base):
    __tablename__ = "move"

    move_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    x_coord = Column(Integer, nullable=False)
    y_coord = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    game_id = Column(Integer, ForeignKey(ActiveGame.game_id), primary_key=True, nullable=False)

    active_game = relationship("ActiveGame", back_populates="move")

    def __repr__(self):
        return f"Move=(move_id={self.move_id!r}, x_coord={self.x_coord!r}, y_coord={self.y_coord!r}, timestamp={self.timestamp!r}, game_id={self.game_id!r})"

# store data of registered users in DB, otherwise use localstorage
engine = create_engine('mysql+pymysql://root:root@localhost:3306/minesweeper_db')
Base.metadata.create_all(engine)


#TODO: Add salts to password encoding
def register(username, password):
    with Session(engine) as session:
        #if username exists, throw error
        #select(player).where(Player.player_id === username)
        if (session.query(Player).filter_by(player_id=username).first()):
            return False
        new_player = Player(
            player_id=username,
            password=hashlib.sha512(password.encode('utf-8')).hexdigest(),
            games_won=0,
            games_lost=0
        )

        session.add(new_player)
        session.commit()
        return True
    

def authenticate(username, password):
    with Session(engine) as session:
        result = session.query(Player).filter_by(player_id=username,
            password=hashlib.sha512(password.encode('utf-8')).hexdigest()).first()
        if (result):
            return True
        else:
            return False
    

def start_game(username, board, data, time):
    with Session(engine) as session:
        new_game = ActiveGame(
            player_id = username,
            game_state = board,
            board_data = data,
            start_time = time
        )

        session.add(new_game)
        session.commit()


#games will be effectively set to null in the db instead of deleted entirely
def end_game(username, player_won):
    with Session(engine) as session:
        if player_won:
            print("won")
            player = session.query(Player).filter(Player.player_id == username).one()
            player.games_won+=1
        else:
            print("lost")
            player = session.query(Player).filter(Player.player_id == username).one()
            player.games_lost+=1
        ended_game = session.query(ActiveGame).filter(ActiveGame.player_id == username).one()
        session.delete(ended_game)
        session.commit()


def make_move(username, board):
    with Session(engine) as session:
        #stmt = select(ActiveGame).where(ActiveGame.player_id == username)
        #game = session.scalars(stmt).one()
        #game.update()
        stmt = update(ActiveGame).where(ActiveGame.player_id == username).values(
            game_state=board).execution_options(synchronize_session="fetch")
        session.execute(stmt)
        session.commit()

def store_move(username, x, y):
    with Session(engine) as session:
        new_move = Move(
            x_coord = x,
            y_coord = y,
            timestamp = time.time(),
            game_id = session.query(ActiveGame).filter(ActiveGame.player_id == username).one().game_id
        )
        session.add(new_move)
        session.commit()

def get_move_list(username):
    with Session(engine) as session:
        game = session.query(ActiveGame).filter(ActiveGame.player_id == username).one().game_id
        #stmt = select(Move.x_coord, Move.y_coord).where(Move.game_id == game).order_by(asc(Move.move_id))
        moves = session.query(Move).filter(Move.game_id == game).order_by(asc(Move.move_id))
        return [(int(move.x_coord), int(move.y_coord)) for move in moves]


def resume_game(username):
    with Session(engine) as session:
        game = session.query(ActiveGame).filter_by(player_id=username).first()
        if game:
            return game.game_state, game.board_data, game.start_time

def reset_game(username, board, data, time):
    with Session(engine) as session:
        #game = session.query(ActiveGame).filter_by(player_id=username).first()
        if (session.query(ActiveGame).filter_by(player_id=username).first()):
            stmt = update(ActiveGame).where(ActiveGame.player_id == username).values(
                game_state = board, board_data = data, start_time = time).execution_options(synchronize_session="fetch")
            session.execute(stmt)
            game = session.query(ActiveGame).filter(ActiveGame.player_id == username).one().game_id
            #Move.query.filter(Move.game_id == game).delete()
            stmt = delete(Move).where(Move.game_id == game)
            session.execute(stmt)
            session.commit()
        else:
            start_game(username, board, data, time)

def update_board(username, data):
    with Session(engine) as session:
        stmt = update(ActiveGame).where(ActiveGame.player_id == username).values(
            board_data = data).execution_options(synchronize_session="fetch")
        session.execute(stmt)
        session.commit()