# Try to import PIL in either of the two ways it can be installed.
import array
import printman.png as png

import printman.qrcode.image.base as base


class PngImage(base.BaseImage):
    """PIL image builder, default format is PNG."""

    def __init__(self, border, width, box_size):
        super(PngImage, self).__init__(border, width, box_size)
        self.kind = "PNG"
        self.pixelsize = (self.width + self.border * 2) * self.box_size
        self.pixels = [array.array("c", "1" * self.pixelsize) for a in range(self.pixelsize)]

    def drawrect(self, row, col):
        start_x = (col + self.border) * self.box_size
        start_y = (row + self.border) * self.box_size
        for y in range(start_y, start_y + self.box_size):
            for x in range(start_x, start_x + self.box_size):
                self.pixels[y][x] = "0"

    def save(self, stream, kind=None):
        if kind is None:
            kind = self.kind
        assert kind == "PNG"
        writer = png.Writer(width=self.pixelsize, height=self.pixelsize, 
                            alpha=False, greyscale=True, bitdepth=1)
        writer.write(stream, self.pixels)