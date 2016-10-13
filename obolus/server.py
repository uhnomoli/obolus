# -*- coding: utf-8 -*-

import asyncio
from os import getpid, kill
import signal
from sys import exit

from utils import Buffer, clean_string, dirty_string


class Server:
    def __init__(self, port):
        self.port = port
        self.users = {}

        self.pid = getpid()
        self.loop = asyncio.get_event_loop()

        self.loop.add_signal_handler(signal.SIGINT, self.close)
        self.loop.add_signal_handler(signal.SIGTERM, self.close)

        asyncio.ensure_future(self.listen(), loop = self.loop)

        self.loop.run_forever()


    def close(self):
        Buffer.esc('[DL][1:HPA]')
        Buffer.write('::  Shutting down\n')

        for reader, writer in self.users.values():
            writer.write(dirty_string('::  Server shutting down'))
            writer.write_eof()

        self.loop.stop()
        exit(0)

    def broadcast(self, message):
        Buffer.write('Sending message: {}\n'.format(message))

        for reader, writer in self.users.values():
            writer.write(dirty_string(message))

    async def connect(self, reader, writer):
        Buffer.write('User connected\n')

        user = writer.get_extra_info('peername')
        self.users[user] = (reader, writer)

        while not reader.at_eof():
            message = await reader.readline()

            if message:
                self.broadcast(clean_string(message))

        Buffer.write('User disconnected\n')

        del self.users[user]
        writer.write_eof()

    async def listen(self):
        Buffer.write('::  Listening\n')

        self.server = await asyncio.start_server(
            self.connect, 'localhost', self.port)

