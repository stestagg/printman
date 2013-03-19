import datetime
import random

from google.appengine.ext import db

import printman.board
import printman.game


class SavedGame(db.Model):
  save_data = db.BlobProperty()
  secret = db.ByteStringProperty()
  last_turn_time = db.DateTimeProperty()


def get_secret():
    return "%08x" % random.getrandbits(32)


def _get_saved_game(key):
    game_id, secret = key.split(".", 1)
    game_id = long(game_id)

    game_key = db.Key.from_path("SavedGame", game_id)
    game = db.get(game_key)
    assert game.secret == secret
    return game


TURN_TIME = datetime.timedelta(days=1)


def get_game(key, update=False):
    saved_game = _get_saved_game(key)
    game = printman.game.Board.load(saved_game.save_data)
    now = datetime.datetime.now()

    if update:
        modified = False
        if saved_game.last_turn_time is None:
            modified = True
            saved_game.last_turn_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        else:
            while saved_game.last_turn_time + TURN_TIME < now:
                modified=True
                try:
                    game.do_turn()
                except AssertionError:
                    pass
                saved_game.last_turn_time += TURN_TIME
        if modified:
            saved_game.save_data = game.dump()
            db.put(saved_game)
    return game


def new_game(game_type, key=None):
    cls = getattr(printman.board, game_type)
    assert issubclass(cls, printman.game.Board), cls
    game = cls()
    if key is None:
        saved_game = SavedGame(secret=get_secret())
    else:
        saved_game = _get_saved_game(key)
    saved_game.save_data=game.dump()
    key = db.put(saved_game)
    game_id = key.id()
    return "%s.%s" % (game_id, saved_game.secret) 


def update_game(key, game):
    saved_game = _get_saved_game(key)
    saved_game.save_data = game.dump()
    db.put(saved_game)