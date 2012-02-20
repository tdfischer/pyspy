#!/usr/bin/env python
import socket
import time
import struct
import binascii
import string
from twisted.internet.protocol import ConnectedDatagramProtocol, Factory
from twisted.internet import reactor

__all__ = ['GamespyProtocol', 'GamespyClient']

class GamespyProtocol(ConnectedDatagramProtocol):
    def __init__(self, host, port):
        self.__host = socket.gethostbyname(host)
        self.__port = port
        self.__players = []
        self.__tags = {}
        self.__token = 0

    def startProtocol(self):
        self.transport.connect(self.__host, self.__port)
        self.sendHello()

    def sendHello(self):
        self._send('!BBBi', 0xfe, 0xfd, 0x09, time.time())

    def sendInfoQuery(self):
        self._send('!BBBiiI', 0xFE, 0XFD, 0x00, time.time(), self.__token, 0xFFFFFF01)

    def _send(self, fmt, *args):
        msg = struct.pack(fmt, *args)
        self.transport.write(msg)

    def datagramReceived(self, data, addr):
        type, = struct.unpack('!B', data[0])
        if type == 0x09:
            # Clamp data size to exactly 16 bytes
            data = data[1:].ljust(15, '\0')[0:15]
            self.__seqnum,token = struct.unpack('!i11s', data)
            validChars = "0123456789-"
            self.__token = int(''.join(c for c in token if c in validChars))
            self.sendInfoQuery()
        elif type == 0:
            tokens, players = data[5:].split('\x01',1)
            tokens = tokens.split('\x00')
            players = players.split('\x00')[:-1]
            ret = {}
            isKey = True
            key = None
            for t in tokens:
                if isKey:
                    key = t
                    isKey = False
                else:
                    ret[key] = t
                    isKey = True
            self.__tags = ret
            playerList = []
            isPlayer = False
            for p in players:
                if (len(p) == 0):
                    continue
                if isPlayer:
                    playerList.append(p)
                    isPlayer = False
                else:
                    isPlayer = True
            self.__players = playerList

    def tags(self):
        return self.__tags

    def players(self):
        return self.__players

class GamespyClient(object):
    def __init__(self, host, port):
        self.__proto = GamespyProtocol(host, port)
        self.__listener = reactor.listenUDP(0, self.__proto)

    def update(self):
        self.__proto.sendHello()
        reactor.doIteration(100)
        self.__proto.sendInfoQuery()
        reactor.doIteration(100)

    def players(self):
        return self.__proto.players()

    def tags(self):
        return self.__proto.tags()
