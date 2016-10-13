# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime as dt
from os import environ as env, getpid, kill
import signal
from shutil import get_terminal_size
from sys import exit

from utils import Buffer, clean_string, dirty_string


class Client:
    def __init__(self, ip, port, channel):
        self.ip = ip
        self.port = port
        self.channel = channel
        self.nick = env.get('USER', None)

        if not self.nick:
            raise EnvironmentError('Missing environment variable')

        self.pid = getpid()
        self.loop = asyncio.get_event_loop()
        self.columns, self.rows = get_terminal_size()
        self.buffer = Buffer(self.columns)

        self.loop.add_signal_handler(signal.SIGINT, self.close)
        self.loop.add_signal_handler(signal.SIGTERM, self.close)

        asyncio.ensure_future(self.listen(), loop = self.loop)

        self.loop.run_forever()


    def close(self):
        Buffer.esc('[DL][1:HPA]')
        Buffer.flush()

        self.loop.stop()
        exit(0)

    def send(self, message):
        self.writer.write(dirty_string('({:%H:%M:%S}) {:>8} › {}'.format(
            dt.now(), self.nick, message)))

    async def input(self):
        while True:
            self.buffer.reset()

            Buffer.write('> ')
            Buffer.flush()

            while True:
                key = await self.loop.run_in_executor(None, Buffer.getch)

                if key in ('\x03', '\x04'):
                    kill(self.pid, signal.SIGTERM)

                    return
                if key == '\x0A' and self.buffer.length:
                    if self.buffer.multiline:
                        Buffer.esc('[{}:CUU]', self.buffer.lines - 1)

                    Buffer.esc('[{}:DL][1:HPA]', self.buffer.lines)
                    Buffer.flush()

                    self.loop.call_soon(self.send, self.buffer.content)

                    break

                code = ord(key[0])

                if code == 27:
                    # Handle escape sequences
                    pass
                if 32 <= code <= 126:
                    Buffer.write(key)
                    Buffer.flush()

                    self.buffer += key
                if code == 127 and self.buffer.length:
                    if self.buffer.index == 1:
                        Buffer.esc('[CUU]')

                    self.buffer.backspace()

                    Buffer.esc('[{}:HPA][EL]', self.buffer.index)
                    Buffer.flush()

    async def listen(self):
        Buffer.write('::  Connecting\n')

        self.reader, self.writer = await asyncio.open_connection(
            self.ip, self.port)

        asyncio.ensure_future(self.input(), loop = self.loop)

        while not self.reader.at_eof():
            message = await self.reader.readline()

            if message:
                message = clean_string(message)
                message = Buffer(self.columns, message)

                if self.buffer.multiline:
                    Buffer.esc('[{}:CUU]', self.buffer.lines - 1)

                Buffer.esc('[{}:IL][1:HPA]', message.lines)
                Buffer.write('{}\n', message.content)

                if self.buffer.multiline:
                    Buffer.esc('[{}:CUD]', self.buffer.lines - 1)

                Buffer.esc('[{}:HPA]', self.buffer.index)
                Buffer.flush()

        kill(self.pid, signal.SIGTERM)

