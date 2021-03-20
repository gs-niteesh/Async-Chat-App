import urwid
import random

class ColorSelector:
    COLORS = [
              urwid.AttrSpec('default', 'dark red'),
              urwid.AttrSpec('default', 'dark blue'),
              urwid.AttrSpec('default', 'dark cyan'),
              urwid.AttrSpec('default', 'dark green'),
              urwid.AttrSpec('default', 'dark magenta')
             ]

    @staticmethod
    def get_color_attr():
        return random.choice(ColorSelector.COLORS)
