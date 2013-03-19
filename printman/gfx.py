import itertools
import math
import os
import png
import sys

import game
import board

OUT_DIR = "./"


def saveb(bits, w, h, name):
	writer = png.Writer(width=w, height=h, greyscale=True, bitdepth=1)
	with open(os.path.join(OUT_DIR, "%s.png" % (name, )), "wb") as fh:
		writer.write(fh, bits)


def save(bits, w, h, name):
	writer = png.Writer(width=w, height=h, alpha=False, greyscale=True, bitdepth=1)
	with open(os.path.join(OUT_DIR, "%s.png" % (name, )), "wb") as fh:
		writer.write(fh, bits)


def to_alpha(rows):
	return [itertools.chain(*zip([0] * len(r), [0 if c else 1 for c in r])) for r in rows]


def pill(size):
	center = size/2.0
	radius_2 = ((size/5.0) - 1) ** 2

	def in_circle(x, y):
		dist = ((x + 0.5) - center) ** 2 + ((y + 0.5) - center) ** 2
		return dist < radius_2
	rows = []
	for y in range(size):
		row = [0] * size
		for x in range(size):
			val = in_circle(x, y)
			row[x] = (0 if val else 1)
		rows.append(row)
	return rows


def pacman(size, facing):
	center = size/2.0
	radius_2 = (center ) ** 2

	def in_circle(x, y):
		dist = ((x + 0.5) - center) ** 2 + ((y + 0.5) - center) ** 2
		return dist < radius_2
	def in_mouth(x, y):
		if facing == game.UP:
			return y <= min(x, (size-1)-x)
		if facing == game.LEFT:
			return x <= min(y, (size-1)-y)
		if facing == game.RIGHT:
			return min(y, (size-1)-y) >= (size-1) - x
		if facing == game.DOWN:
			return min(x, (size-1)-x) >= (size-1) - y

	rows = []
	for y in range(size):
		row = []
		for x in range(size):
			val = in_circle(x, y) and not in_mouth(x, y)
			row.append(0 if val else 1)
		rows.append(row)
	return rows


EYES3 = {
	game.DOWN: "010 111 101 000".split(),
	game.LEFT: "010 011 011 010".split(),
	game.RIGHT: "010 110 110 010".split(),
	game.UP: "000 101 111 010".split()
}


def monster(size, facing):
	center = size/2.0
	radius = center
	waves = 3 if size > 17 else 2
	factor = (waves + 0.5) * (2*math.pi) / (size)
	sin_scale = 1 if size < 15 else 1.5

	def in_circle(x, y):
		dist = math.sqrt(((x + 0.5) - center) ** 2 + ((y + 0.5) - center) ** 2)
		return dist < radius

	def above_hemline(x, y):
		hemline = (size - 2) + (math.sin((factor * (x)))*sin_scale)
		return y < hemline
	rows = []
	for y in range(size):
		row = []
		for x in range(size):
			val = in_circle(x, min(y, center)) and above_hemline(x, y)
			row.append(0 if val else 1)
		rows.append(row)

	offs = {game.LEFT: 2, game.RIGHT: 0, game.UP: 1, game.DOWN: 1}[facing]
	eye1x = (size/3) - offs
	eye2x = (2*size/3) - offs
	eyey = size/3
	for y, row in enumerate(EYES3[facing]):
		for x, bit in enumerate(row):
			rows[eyey + y][eye1x + x] |= int(bit)
			rows[eyey + y][eye2x + x] |= int(bit)
	return rows


def draw_wall(size, bx, ax, by, ay):	
	return cells


def erode(data, edge):
	def any_bits(x, y):
		if data[y][x]:
			return True
		if y == 0 or x == 0:
			return edge
		if data[y][x-1] or data[y-1][x]:
			return True
		try:
			if data[y+1][x]:
				return True
			if data[y][x+1]:
				return True
		except IndexError:
			return edge
		return False
	new = []
	for y, row in enumerate(data):
		new_row = [0] * len(row)
		new.append(new_row)
		for x, bit in enumerate(row):
			new_row[x] = (1 if any_bits(x, y) else 0)
	return new


def outline(data):
	def any_different(x, y, test):
		if y > 0 and data[y-1][x] != test:
			return True
		if x > 0 and data[y][x-1] != test:
			return True
		try:
			if data[y+1][x] != test:
				return True
		except IndexError:
			pass
		try:
			if data[y][x+1] != test:
				return True
		except IndexError:
			pass
		return False
	new = []
	for y, row in enumerate(data):
		new_row = [0] * len(row)
		new.append(new_row)
		for x, bit in enumerate(row):
			new_row[x] = (data[y][x] if any_different(x, y, data[y][x]) else 1)
	return new


def invert(grid):
	return [[0 if c else 1 for c in row] for row in grid]

def pattern(w, h):
	return [[int((x + y) % 3 == 0) for x in range(w)] for y in range(h)]

def mask(a, b):
	rows = []
	for arow, brow in zip(a, b):
		row = [0] * len(arow)
		rows.append(row)
		for x, (ac, bc) in enumerate(zip(arow, brow)):
			row[x] = (ac | bc)
	return rows

def add(a, b):
	rows = []
	for arow, brow in zip(a, b):
		row = [0] * len(arow)
		rows.append(row)
		for x, (ac, bc) in enumerate(zip(arow, brow)):
			row[x] = (ac & bc)
	return rows

LOGO_WIDTH = 333
LOGO_HEIGHT = 45
QR_SIZE = 74

def draw_grid(grid, size):
	cell_size = int(size / grid.WIDTH)
	image_width = grid.WIDTH * cell_size

	logo_padding = cell_size
	logo_width_adj = cell_size * (grid.WIDTH - 2)
	header_height = LOGO_HEIGHT + logo_padding * 2

	footer_height = QR_SIZE + cell_size
	footer_top = grid.HEIGHT * cell_size + header_height

	image_height = footer_top + footer_height

	def is_wall(x, y):
		if x < 0 or y < 0 or x >= grid.WIDTH or y >= grid.HEIGHT:
			return False
		return (x, y) in grid.WALLS

	empty_cell = [[1] * cell_size for i in range(cell_size)]
	full_cell = [[0] * cell_size for i in range(cell_size)]

	cells = [[] for i in range(image_height)]

	for y in range(header_height):
		for x in range(image_width):
			val = 1 if (y > logo_padding 
						and y < LOGO_HEIGHT + logo_padding 
						and x > logo_padding 
						and x < logo_width_adj + logo_padding) else 0
			cells[y].append(val)

	for y in range(footer_height):
		cells[footer_top + y].extend(
			[0] * image_width)

	for y in range(footer_top, footer_top + footer_height - cell_size):
		for x in range(image_width - QR_SIZE - cell_size, image_width - cell_size):
			cells[y][x] = 1

	for y in range(grid.HEIGHT):
		for x in range(grid.WIDTH):
			for py, row in enumerate(full_cell if is_wall(x, y) else empty_cell):
				cells[(y * cell_size) + header_height + py].extend(row)
	for i in range(4):
		cells = erode(cells, True)
	cells = invert(cells)
	for i in range(2):
		cells = erode(cells, False)
	cells = invert(cells)
	out = outline(cells)
	cells = erode(cells, True)
	cells = erode(cells, True)

	patt = pattern(grid.WIDTH * cell_size, image_height)

	final = add(mask(patt, cells), out)
	saveb(final, grid.WIDTH * cell_size, image_height, "%s/board" % grid.__name__)


def main():
	for b in [game.MetaBoard, board.MediumBoard, board.SmallBoard, board.PracticeBoard, board.ClassicBoard]:
		b.setup()
		cell_size = int(384 / b.WIDTH)
		draw_grid(b, 384)
		save(pill(cell_size), cell_size, cell_size, "%s/pill" % b.__name__)
		save(monster(16, game.DOWN), 16, 16, "favicon")
		for pos in (game.LEFT, game.RIGHT, game.UP, game.DOWN):
			name = {game.LEFT: "left", game.RIGHT: "right", 
					game.UP: "up", game.DOWN: "down", }
			save(pacman(cell_size, pos), cell_size, cell_size, 
				 "%s/pacman.%s" % (b.__name__, name[pos]))
			save(monster(cell_size, pos), cell_size, cell_size, 
				 "%s/monster.%s" % (b.__name__, name[pos]))

if __name__ == "__main__":
	sys.exit(main())
		
		



