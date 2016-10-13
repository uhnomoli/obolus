# -*- coding: utf-8 -*-

from argparse import ArgumentParser

from client import Client
from server import Server


class Obolus:
    def __init__(self):
        parser = ArgumentParser()

        modes = parser.add_subparsers(
            dest = 'mode',
            title = 'Modes', description = 'Available obolus modes.')
        modes.required = True

        server = modes.add_parser('server')
        server.add_argument('-p', '--port',
            nargs = '?', default = 10110, type = int,
            help = 'The port the server will listen on.')
        server.set_defaults(func = self.listen)

        client = modes.add_parser('client')
        client.add_argument('ip',
            help = 'IP of obolus server to connect to.')
        #client.add_argument('channel',
        #    help = 'Channel to join on obolus server.')
        client.add_argument('-p', '--port',
            default = 10110, type = int,
            help = 'Port obolus server is listening on.')
        client.set_defaults(func = self.connect)

        self.opts = parser.parse_args()
        self.opts.func()


    def listen(self):
        Server(self.opts.port)

    def connect(self):
        Client(self.opts.ip, self.opts.port, 'letsgo')

