#!/usr/bin/env python

import webapp2
import binascii
import hashlib
import os
import jinja2
import cStringIO as StringIO

from google.appengine.api import memcache

import printman.qrcode.main as qrcode
import printman.board
import printman.game
import printman.store


PAGE_WIDTH = 384


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))


class Page(webapp2.RequestHandler):

    def render_template(self, name, **context):
        template = jinja_environment.get_template(name)
        self.response.out.write(template.render(context))

    def render_board(self, board, key=None, **extra):
        if board.mode == printman.game.WON:
            return self.render_meta(board, "won", key=key)
        if board.mode == printman.game.GAME_OVER:
            return self.render_meta(board, "game_over", key=key)
        return self._render_board(board, key=key, **extra)

    def render_meta(self, board, image, key=None):
        host = self.request.environ["HTTP_HOST"]
        return self._render_board(
            board, image=image, host=host,
            layout=printman.game.MetaBoard, key=key)

    def _render_board(self, board, **extra):
        host = self.request.environ["HTTP_HOST"]
        layout = extra.get("layout", type(board))
        cell_size = int(PAGE_WIDTH/layout.WIDTH)
        def xpos(x):
            return cell_size * x

        def ypos(y):
            return LOGO_HEIGHT + (2*cell_size) + y * cell_size
        
        args = {
            "board": board, 
            "xpos": xpos, 
            "ypos": ypos,
            "LEFT": printman.game.DIRN_NAMES[printman.game.LEFT],
            "RIGHT": printman.game.DIRN_NAMES[printman.game.RIGHT],
            "UP": printman.game.DIRN_NAMES[printman.game.UP],
            "DOWN": printman.game.DIRN_NAMES[printman.game.DOWN],
            "layout": layout,
            "cell_size": cell_size, 
            "str": str,
            "host": host,
            "controls": False,
        }
        args.update(extra)
        return self.render_template("draw.html", **args)


LOGO_HEIGHT = 45


class PlayHandler(Page):
    
    def get(self):
        game_key = self.request.get("g")
        game = printman.store.get_game(game_key)
        if game.mode == printman.game.WON or game.mode == printman.game.GAME_OVER:
            return self.render_template("new_game.html", key=game_key, rurl="/started/")
        return self.render_template("move.html", board=game, key=game_key)


class SetDirnHandler(Page):

    def get(self):
        dirn = self.request.get("dirn")
        key = self.request.get("key")
        game = printman.store.get_game(key, update=True)
        game.dirn = printman.game.DIRN_IDS[dirn]
        printman.store.update_game(key, game)
        return self.render_template("set_dirn.html", dirn=dirn)


class StartHandler(Page):
    
    def get(self):
        game_type = self.request.get("game")
        rurl = self.request.get("return_url")
        key = self.request.get("key", None)
        assert game_type and rurl

        game_key = printman.store.new_game(game_type, key=key)
        return self.redirect(str("%s?config[access_token]=%s" % (rurl, game_key)))


class StartedHandler(Page):

    def get(self):
        return self.render_template("started.html")


class EditionHandler(Page):

    def get(self):
        game_key = self.request.get("access_token", None)
        if game_key is None:
            self.abort(400, "Access token not supplied")
        game = printman.store.get_game(game_key, update=True)
        self.response.headers['ETag'] = hashlib.sha224("%s.%s" % (game_key, game.turn)).hexdigest()
        return self.render_board(game, key=game_key)


class DummyGameHandler(Page):

    def get(self):
        game_key = self.request.get("config[access_token]")
        game = printman.store.get_game(game_key, update=True)
        return self.render_board(game, key=game_key, controls=True)


class QRHandler(Page):

    def get(self):
        game_key = self.request.get("access_token")
        assert len(game_key) > 0
        qr_data = memcache.get('%s:qrcode' % game_key)
        if qr_data is None:
            qr = qrcode.QRCode(box_size=2, border=0, version=5)
            host = self.request.environ["HTTP_HOST"]
            qr.add_data("http://%s/p/?g=%s" % (host, game_key))
            qr.make()
            im = qr.make_image()
            buf = StringIO.StringIO()
            im.save(buf)
            qr_data = buf.getvalue()
            memcache.add("%s:qrcode" % game_key, qr_data)
        self.response.headers["Content-type"] = "image/png"
        self.response.out.write(qr_data)


class SampleHandler(Page):

    # This is kinda ugly, but works..
    SAMPLE_GAME = """(S'ClassicBoard'\np1\nI1\nI84\nI1480\nc__builtin__\nset\np2\n((lp3\n(I15\nI27\ntp4\na(I12\nI1\ntp5\na(I15\nI20\ntp6\na(I20\nI20\ntp7\na(I17\nI20\ntp8\na(I15\nI1\ntp9\na(I21\nI9\ntp10\na(I25\nI1\ntp11\na(I21\nI6\ntp12\na(I2\nI5\ntp13\na(I26\nI6\ntp14\na(I8\nI5\ntp15\na(I3\nI24\ntp16\na(I10\nI8\ntp17\na(I6\nI7\ntp18\na(I5\nI5\ntp19\na(I11\nI5\ntp20\na(I6\nI25\ntp21\na(I1\nI28\ntp22\na(I24\nI1\ntp23\na(I21\nI12\ntp24\na(I1\nI1\ntp25\na(I4\nI5\ntp26\na(I3\nI23\ntp27\na(I15\nI21\ntp28\na(I7\nI5\ntp29\na(I10\nI23\ntp30\na(I6\nI26\ntp31\na(I21\nI18\ntp32\na(I12\nI22\ntp33\na(I13\nI23\ntp34\na(I18\nI25\ntp35\na(I26\nI1\ntp36\na(I3\nI1\ntp37\na(I4\nI26\ntp38\na(I10\nI29\ntp39\na(I12\nI8\ntp40\na(I1\nI21\ntp41\na(I17\nI8\ntp42\na(I24\nI8\ntp43\na(I21\nI21\ntp44\na(I1\nI26\ntp45\na(I25\nI5\ntp46\na(I21\nI2\ntp47\na(I2\nI1\ntp48\na(I26\nI2\ntp49\na(I5\nI1\ntp50\na(I11\nI29\ntp51\na(I15\nI26\ntp52\na(I12\nI2\ntp53\na(I14\nI5\ntp54\na(I18\nI5\ntp55\na(I24\nI5\ntp56\na(I21\nI8\ntp57\na(I2\nI23\ntp58\na(I26\nI8\ntp59\na(I21\nI5\ntp60\na(I26\nI7\ntp61\na(I18\nI1\ntp62\na(I4\nI1\ntp63\na(I9\nI7\ntp64\na(I6\nI4\ntp65\na(I9\nI20\ntp66\na(I7\nI1\ntp67\na(I17\nI1\ntp68\na(I18\nI6\ntp69\na(I16\nI26\ntp70\na(I21\nI11\ntp71\na(I20\nI5\ntp72\na(I3\nI5\ntp73\na(I23\nI5\ntp74\na(I6\nI1\ntp75\na(I16\nI1\ntp76\na(I5\nI20\ntp77\na(I12\nI4\ntp78\na(I11\nI20\ntp79\na(I10\nI20\ntp80\na(I25\nI20\ntp81\na(I16\nI20\ntp82\na(I21\nI17\ntp83\na(I12\nI23\ntp84\na(I19\nI1\ntp85\na(I21\nI14\ntp86\na(I2\nI29\ntp87\na(I1\nI3\ntp88\na(I9\nI8\ntp89\na(I23\nI8\ntp90\na(I9\nI29\ntp91\na(I6\nI2\ntp92\na(I5\nI26\ntp93\na(I1\nI20\ntp94\na(I7\nI20\ntp95\na(I22\nI20\ntp96\na(I21\nI20\ntp97\na(I12\nI20\ntp98\na(I21\nI1\ntp99\na(I26\nI3\ntp100\na(I8\nI29\ntp101\na(I5\nI29\ntp102\na(I12\nI3\ntp103\na(I17\nI5\ntp104\na(I15\nI22\ntp105\na(I15\nI3\ntp106\na(I20\nI1\ntp107\na(I2\nI20\ntp108\na(I1\nI4\ntp109\na(I23\nI20\ntp110\na(I15\nI4\ntp111\na(I21\nI4\ntp112\na(I26\nI4\ntp113\na(I23\nI1\ntp114\na(I3\nI26\ntp115\na(I18\nI26\ntp116\na(I9\nI6\ntp117\na(I6\nI5\ntp118\na(I4\nI29\ntp119\na(I10\nI5\ntp120\na(I16\nI5\ntp121\na(I11\nI8\ntp122\na(I16\nI8\ntp123\na(I13\nI5\ntp124\na(I19\nI5\ntp125\na(I18\nI7\ntp126\na(I21\nI10\ntp127\na(I17\nI26\ntp128\na(I22\nI1\ntp129\na(I21\nI7\ntp130\na(I3\nI25\ntp131\na(I9\nI1\ntp132\na(I6\nI6\ntp133\na(I12\nI5\ntp134\na(I11\nI23\ntp135\na(I15\nI8\ntp136\na(I6\nI24\ntp137\na(I21\nI16\ntp138\na(I1\nI29\ntp139\na(I18\nI8\ntp140\na(I25\nI8\ntp141\na(I15\nI5\ntp142\na(I21\nI13\ntp143\na(I2\nI26\ntp144\na(I1\nI2\ntp145\na(I15\nI28\ntp146\na(I7\nI29\ntp147\na(I8\nI1\ntp148\na(I3\nI20\ntp149\na(I8\nI20\ntp150\na(I6\nI3\ntp151\na(I11\nI1\ntp152\na(I21\nI19\ntp153\na(I12\nI21\ntp154\na(I18\nI24\ntp155\na(I10\nI1\ntp156\na(I4\nI20\ntp157\na(I19\nI20\ntp158\na(I24\nI20\ntp159\na(I21\nI15\ntp160\na(I1\nI22\ntp161\na(I6\nI29\ntp162\na(I15\nI2\ntp163\na(I21\nI22\ntp164\na(I1\nI27\ntp165\na(I22\nI5\ntp166\na(I21\nI3\ntp167\na(I26\nI5\ntp168\na(I22\nI8\ntp169\na(I3\nI29\ntp170\na(I9\nI5\ntp171\na(I18\nI20\ntp172\natRp173\n(dp174\nS'P'\n(S'P'\nI5\nI8\nI0\nS'chase'\np175\nI4927\ntp176\nsS'M'\n(S'M'\nI1\nI8\nI0\nS'fixed'\np177\nI3\ntp178\nsS'O'\n(S'O'\nI18\nI26\nI3\nS'fixed'\np179\nI0\ntp180\nsS'N'\n(S'N'\nI9\nI6\nI2\nS'chase'\np181\nI-1\ntp182\nsI2\n(I1\nI5\ntp183\nt."""

    def get(self):
        board = printman.game.Board.load(self.SAMPLE_GAME)
        return self.render_board(board)


class NewGameHandler(Page):

    def get(self):
        return_url = self.request.get("return_url", "/dummy/")
        return self.render_template("new_game.html", rurl=return_url)


class NextHandler(Page):

    def get(self):
        game_key = self.request.get("access_token", None)
        dirn = self.request.get("dirn", None)
        assert game_key is not None and dirn is not None
        game = printman.store.get_game(game_key, update=True)
        if game.mode == printman.game.NOT_STARTED:
            game.start()
        game.dirn = printman.game.DIRN_IDS[dirn]
        game.do_turn()
        printman.store.update_game(game_key, game)
        return self.redirect("/dummy/?config[access_token]=%s" % (game_key, ))


app = webapp2.WSGIApplication([
    ('/configure/', NewGameHandler),
    ('/edition/', EditionHandler),
    
    ('/dummy/', DummyGameHandler),
    ('/next/', NextHandler),
    
    ('/p/', PlayHandler),
    ('/set_dirn/', SetDirnHandler),
    ('/qr/', QRHandler),
    ('/sample/', SampleHandler),
    ('/start_game/', StartHandler),
    ('/started/', StartedHandler),
], debug=True)
