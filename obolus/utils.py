# -*- coding: utf-8 -*-

from math import ceil
import re
from sys import stdin, stdout
import tty


_ESCAPES = {
    'CUU': 'A',
    'CUD': 'B',
    'CUF': 'C',
    'CUB': 'D',
    'EL':  'K',
    'IL':  'L',
    'DL':  'M',
    'HPA': '`'
}


class Buffer:
    def __init__(self, columns, content = '', pad = 3, limit = 4095):
        self._pad = pad
        self._length = 0
        self._index = self._pad
        self._lines = 1
        self._content = ''

        self.columns = columns
        self.content = content


    def reset(self):
        self._length = 0
        self._index = self._pad
        self._lines = 1
        self._content = ''

    def backspace(self):
        if self._length:
            self.content = self._content[:-1]


    @property
    def length(self):
        return self._length

    @property
    def index(self):
        return self._index

    @property
    def lines(self):
        return self._lines

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, content):
        if self._content != content:
            self._content = content
            self._length = len(self._content)
            self._index = self._length + self._pad
            self._lines = ceil((self._length + self._pad) / self.columns)

            if self.multiline:
                self._index = (self._index - 1) % self.columns + 1


    @property
    def multiline(self):
        return self._lines > 1


    def __add__(self, other):
        self.content = self.content + other

        return self


    @staticmethod
    def getch():
        fd = stdin.fileno()
        old_config = tty.tcgetattr(fd)

        tty.setcbreak(fd)

        new_config = tty.tcgetattr(fd)
        new_config[3] &= ~tty.ISIG

        tty.tcsetattr(fd, tty.TCSANOW, new_config)

        try:
            key = stdin.read(1)

            if key in ('\x0A', '\x0D'):
                key = '\x0A'
            if key == '\x1B':
                key += stdin.read(2)
        finally:
            tty.tcsetattr(fd, tty.TCSADRAIN, old_config)
            tty.tcdrain(fd)

        return key

    @staticmethod
    def flush():
        stdout.flush()

    @staticmethod
    def esc(text, *args):
        def expand(match):
            count, escape = match.group(1, 2)

            count = count if count else ''
            escape = _ESCAPES[escape]

            return '\x1B[{}{}'.format(count, escape)

        if args:
            text = text.format(*args)

        stdout.write(re.sub(r'\[(?:(\d+):)?([A-Z]{1,3})\]', expand, text))

    @staticmethod
    def write(text, *args):
        if args:
            text = text.format(*args)

        stdout.write(text)


def clean_string(text):
    if isinstance(text, bytes):
        text = text.decode('utf-8')

    return text.rstrip()

def dirty_string(text):
    return '{}\n'.format(text).encode('utf-8')

