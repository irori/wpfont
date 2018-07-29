import sys

from bdflib import reader

from charset import codeconv
from smoother import Smoother, SCALE

MARGIN = 8

class Glyph:

    def __init__(self, font, bdf_glyph, unicode):
        self.font = font
        self.bdf_glyph = bdf_glyph
        self.unicode = unicode

    def name(self):
        return self.bdf_glyph.name

    def vectorize(self, smooth=True):
        s = Smoother(self._bitmap())
        if smooth:
            s.smooth()
        return s.vectorize(MARGIN, -self.font.bdf['FONT_DESCENT'] * SCALE)

    def _bitmap(self):
        bitmap = []
        width = self.bdf_glyph.bbW
        for line in self.bdf_glyph.data:
            a = []
            for b in range(width - 1, -1, -1):
                a.append(line & (1 << b) and 1 or 0)
            bitmap.append(a)
        return bitmap


class Font:
    def __init__(self, bdf_filename):
        with open(bdf_filename) as f:
            self.bdf = reader.read_bdf(f)
        self.codeconv = codeconv(self.bdf['CHARSET_REGISTRY'],
                                 self.bdf['CHARSET_ENCODING'])
        self.width = self.bdf[self.bdf['DEFAULT_CHAR']].bbW * SCALE + MARGIN * 2
        self.ascent = self.bdf['FONT_ASCENT'] * SCALE + MARGIN
        self.descent = -self.bdf['FONT_DESCENT'] * SCALE - MARGIN

        # For some reasons, IDEOGRAPHIC SPACE in jiskan24-2003-1.bdf is not
        # really a whitespace. Overwrite it.
        self.bdf[0x2121].data = map(lambda _: 0, self.bdf[0x2121].data)

    def set_ufo_metrics(self, info):
        info.unitsPerEm = self.width
        info.ascender = self.ascent
        info.descender = self.descent
        info.capHeight = self.bdf[0x2354].get_ascent() * SCALE  # FULLWIDTH LATIN CAPITAL LETTER T
        info.xHeight = self.bdf[0x2378].get_ascent() * SCALE  # FULLWIDTH LATIN SMALL LETTER X

    def glyphs(self):
        for cp in self.bdf.codepoints():
            unicode = self.codeconv.unicode(cp)
            if unicode is None:
                print >> sys.stderr, 'Unknown codepoint 0x%x:' % cp
                print >> sys.stderr, self.bdf[cp]
                continue
            yield Glyph(self, self.bdf[cp], unicode)
