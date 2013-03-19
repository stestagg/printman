import os
import base64
import cPickle as pickle
import sys
import collections


def get_distance_cmp((x1, y1), (x2, y2)):
	return ((x2-x1) ** 2) + ((y2 - y1) ** 2)


def closest(to, *options):
	assert len(options) > 0
	_, pos = sorted([(get_distance_cmp(o, to), o) for o in options])[0]
	return pos


LEFT = 0
RIGHT = 1
UP = 2
DOWN = 3

DIRN_NAMES={
	LEFT: "left",
	RIGHT: "right",
	UP: "up",
	DOWN: "down"
}

DIRN_IDS={
	"left": LEFT,
	"right": RIGHT,
	"up": UP,
	"down": DOWN,
}


NOT_STARTED = 0
STARTED = 1
GAME_OVER = 2
WON = 3

class Monster(object):

	SLEEP_TIMES = {
		"M": 0,
		"N": 3,
		"O": 5,
		"P": 7
	}
	MODES = {
		"M": (("fixed", 7), ("chase", 20)),
		"N": (("fixed", 7), ("chase", 20)),
		"O": (("fixed", 5), ("chase", 20)),
		"P":(("fixed", 5), ("chase", 5000))
	}

	CHASE_PROJECTION = {
		"M": 0,
		"N": 4,
		"O": 0,
		"P": 2
	}

	def __init__(self, board, type, x, y):
		self.type = type
		self.board = board
		self.x = x
		self.y = y
		self.dirn = UP
		self.mode = None
		self.mode_time = 0
		self.mode_names = {
			"fixed": self.do_goto_fixed,
			"chase": self.do_chase,
			"sleep": self.do_sleep
		}
		self.set_mode()

	def dump(self):
		return (self.type, self.x, self.y, self.dirn, self.mode, self.mode_time)

	@classmethod
	def load(cls, board, parts):
		tp, x, y, dirn, mode, mode_time = parts
		monster = Monster(board, tp, x, y)
		monster.mode = mode
		monster.dirn = dirn
		monster.mode_time = mode_time
		return monster

	@property
	def position(self):
		return self.x, self.y

	@property
	def dirn_str(self):
		return DIRN_NAMES[self.dirn]

	def set_mode(self):	
		if self.mode is None:
			self.mode = "sleep"
			self.mode_time = self.SLEEP_TIMES[self.type]
		if self.mode_time <= 0:
			remaining = self.board.turn - self.SLEEP_TIMES[self.type]
			while True:
				for mode_name, time in self.MODES[self.type]:
					if remaining - time <= 0:
						break
					remaining -= time
				else: # If remaining > 0, check the next move for options
					continue
				break # If we didn't continue, then exit the loop (remaining <= 0)
			self.mode = mode_name
			self.mode_time = time - remaining

	def do_chase(self):
		if self.move_simple():
			return
		pos = (self.x, self.y)
		options = self.board.MOVEMENT_OPTIONS[pos] - set([self.get_behind()])
		target = self.board.project_position(self.CHASE_PROJECTION[self.type])
		self.set_pos(closest(target, *options))

	def do_sleep(self):
		pass

	def set_pos(self, (x, y)):
		if x == self.x:
			self.dirn = UP if self.y > y else DOWN
		elif y == self.y:
			self.dirn = LEFT if self.x > x else RIGHT
		if (x, y) in self.board.WARP_POINTS:
			x, y = set(self.board.WARP_POINTS - set([(x, y)])).pop()
		self.x = x
		self.y = y

	def get_behind(self):
		if self.dirn == LEFT:
			return self.x+1, self.y
		elif self.dirn == RIGHT:
			return self.x-1, self.y
		elif self.dirn == UP:
			return self.x, self.y+1
		elif self.dirn == DOWN:
			return self.x, self.y-1
		raise AssertionError("What direction?")

	def get_options(self):
		return 

	def move_simple(self):
		pos = (self.x, self.y)
		if pos in self.board.ROOMS:
			options = self.board.MOVEMENT_OPTIONS[pos] | self.board.ROOM_MOVEMENT[pos]
			target = closest(pos, *self.board.MONSTER_EXITS)
			self.set_pos(closest(target, *options))
			return True
		options = self.board.MOVEMENT_OPTIONS[pos] - set([self.get_behind()])
		if len(options) == 1:
			option, = options
			self.set_pos(option)
			return True
		return False

	def do_goto_fixed(self):
		if self.move_simple():
			return
		pos = (self.x, self.y)
		options = self.board.MOVEMENT_OPTIONS[pos] - set([self.get_behind()])
		behind = self.get_behind()
		if len(options) == 2 and behind in options:
			option, = [o for o in options if o != behind]
			self.set_pos(option)
			return
		
		target = self.board.TARGETS[self.type]
		self.set_pos(closest(target, *options))

	def do_turn(self):
		if self.mode_time <= 0:
			self.set_mode()
		self.mode_names[self.mode]()
		self.mode_time -= 1


class Chars(object):
	BOUNDARIES = "-+|Xx"
	EXITS = "="
	PACMAN = "c"
	MONSTERS = "MNOP"
	WARP_POINTS = "*"
	ROOM = "^"
	PILL = "."
	NAVIGABLE = PACMAN + PILL + MONSTERS + " " + WARP_POINTS


class Board(object):
	
	BOARD = NotImplemented
	TARGETS = NotImplemented
	IS_SETUP = False

	@classmethod
	def setup(cls):
		if cls.IS_SETUP:
			return
		cls.BOARD = cls.BOARD.strip().split("\n")
		navigable = set()
		movement_options = collections.defaultdict(set)
		room_movement = collections.defaultdict(set)
		cls.WIDTH = 0
		cls.HEIGHT = len(cls.BOARD)
		pills = set()
		rooms = set()
		warp_points = set()
		walls = set()
		monster_exits = set()
		cls.MONSTERS = {}

		for y, row in enumerate(cls.BOARD):
			cls.WIDTH = max(cls.WIDTH, len(row))
			for x, cell in enumerate(row):
				if cell in Chars.NAVIGABLE:
					navigable.add((x, y))
					for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
						movement_options[x + dx, y+dy].add((x, y))
				if cell in Chars.PILL:
					pills.add((x, y))
				if cell in Chars.ROOM or cell in Chars.MONSTERS:
					rooms.add((x, y))
					for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
						room_movement[x + dx, y+dy].add((x, y))
				if cell in Chars.EXITS:
					for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
						room_movement[x + dx, y+dy].add((x, y))
				if cell in Chars.PACMAN:
					cls.INITIAL_POSITION = (x, y)
				if cell in Chars.EXITS:
					monster_exits.add((x, y))
				if cell in Chars.BOUNDARIES:
					walls.add((x, y))
				if cell in Chars.WARP_POINTS:
					warp_points.add((x, y))
				if cell in Chars.MONSTERS:
					cls.MONSTERS[cell] = (x, y)

		cls.NAVIGABLE = frozenset(navigable)
		cls.MOVEMENT_OPTIONS = collections.defaultdict(frozenset, {k: frozenset(v) for k, v in movement_options.iteritems()})
		cls.ROOM_MOVEMENT = collections.defaultdict(frozenset, {k: frozenset(v) for k, v in room_movement.iteritems()})
		cls.WARP_POINTS = frozenset(warp_points)
		cls.PILLS = frozenset(pills)
		cls.ROOMS = frozenset(rooms)
		cls.WALLS = frozenset(walls)
		cls.MONSTER_EXITS = frozenset(monster_exits)
		cls.IS_SETUP = True

	def __init__(self):
		type(self).setup()
		self.turn = 1
		self.mode = NOT_STARTED
		self.score = 0
		self.pills = set(self.PILLS)
		self.monsters = {t: Monster(self, t, x, y) for t, (x, y) in self.MONSTERS.iteritems()}
		self.dirn = RIGHT
		self.position = self.INITIAL_POSITION

	@property
	def name(self):
		return type(self).__name__

	@property
	def dirn_str(self):
		return DIRN_NAMES[self.dirn]

	@classmethod
	def board_by_name(cls, name):
		for b in Board.__subclasses__():
			if b.__name__ == name:
				return b
		raise KeyError("No board with name '%s' could be found" % name)

	def dump(self):
		return pickle.dumps((
			type(self).__name__, 
			self.mode, 
			self.turn, 
			self.score, 
			self.pills, 
			{t: m.dump() for t, m in self.monsters.iteritems()},
			self.dirn, 
			self.position))

	@classmethod
	def load(cls, data):
		bits = pickle.loads(data)
		board_type, mode, turn, score, pills, monsters, dirn, position = bits
		board = Board.board_by_name(board_type)()
		board.mode = mode
		board.turn = turn
		board.score = score
		board.pills = pills
		board.monsters = {t: Monster.load(board, d) for t, d in monsters.iteritems()}
		board.dirn = dirn
		board.position = position
		return board

	def start(self):
		assert self.mode == NOT_STARTED or self.mode == STARTED
		self.mode = STARTED

	def do_turn(self):
		if self.mode == NOT_STARTED:
			self.mode = STARTED
		if self.mode != STARTED:
			raise AssertionError("Game not in progress")
		self.turn += 1
		new_pos = self.project_position(1)
		if new_pos in self.WARP_POINTS:
			new_pos = set(self.WARP_POINTS - set([new_pos])).pop()
			self.position = new_pos
		elif new_pos in self.MOVEMENT_OPTIONS[self.position]:
			self.position = new_pos
		if new_pos in self.pills:
			self.pills.remove(new_pos)
			if len(self.pills) == 0:
				self.score += 500
				self.mode = WON
				return 
			self.score += 20
		for monster in self.monsters.values():
			if monster.position == self.position:
				self.mode = GAME_OVER
				return
			monster.do_turn()
			if monster.position == self.position:
				self.mode = GAME_OVER
				return

	def project_position(self, n):
		x, y = self.position
		if self.dirn == UP:
			return x, y - n
		elif self.dirn == DOWN:
			return x, y + n
		elif self.dirn == LEFT:
			return x - n, y
		elif self.dirn == RIGHT:
			return x + n, y
		raise AssertionError("What direction?")

	def to_string(self):
		output = []
		monsters = [(m.x, m.y) for m in self.monsters.values()]
		for y in range(self.HEIGHT):
			row = ""
			for x in range(self.WIDTH):
				if (x, y) == self.position:
					row += {LEFT: ">", RIGHT: "<", 
						   UP: "V", DOWN: "^"}[self.dirn]
					continue
				if (x, y) in monsters:
					row += "M"
				elif (x, y) in self.pills:
					row += "."
				else:
					row += ("X" if (x, y) in self.WALLS else " ") 
			output.append(row)
		output.append("Turn: %s" % self.turn)
		output.append("Score: %s" % self.score)
		return "\n".join(output)


class MetaBoard(Board):
	BOARD = """
+------------++------------+
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
|                          |
+--------------------------+
"""

MetaBoard.setup()