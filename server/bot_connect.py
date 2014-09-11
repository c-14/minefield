import argparse
import logging
import time
import threading

from socketIO_client import BaseNamespace, SocketIO

from logs import init_logging
from bot import Bot

logger = logging.getLogger('bot')


class MinefieldNamespace(BaseNamespace):
    def on_wait(self):
        pass

    def on_phase_one(self, data):
        tiles = data['tiles']
        logger.info('my tiles: %s', ' '.join(sorted(tiles)))
        dora_ind = data['dora_ind']
        logger.info('dora indicator: %s', dora_ind)
        east = data['east'] == data['you']
        options = {
            'fanpai_winds': ['X1' if east else 'X3'],
            'dora_ind': dora_ind,
        }
        self.me = data['you']
        self.bot = Bot(tiles=tiles, options=options)

        self.build_hand()

    def build_hand(self):
        def build():
            logger.info('thinking about my hand...')
            tenpai = self.bot.choose_tenpai()
            logger.info('my hand: %s', ' '.join(tenpai))
            self.emit('hand', tenpai)
        thread = threading.Thread(target=build)
        thread.start()

    def on_wait_for_phase_two(self, data):
        pass

    def on_phase_two(self, data):
        pass

    def on_your_move(self, data):
        tile = self.bot.discard()
        logger.info('discarding: %s', tile)
        self.emit('discard', tile)

    def on_discarded(self, data):
        if data['player'] != self.me:
            self.bot.opponent_discard(data['tile'])

    def on_ron(self, data):
        if data['player'] == self.me:
            logger.info('I won!\n%r', data)
        else:
            logger.info('I lost!\n%r', data)
        self.disconnect()

    def on_draw(self, data):
        logger.info('Draw!')
        self.disconnect()


def bot_connect(host, port, nick):
    logger.info('Starting bot client')
    socket = SocketIO(host, port, wait_for_connection=False)
    logger.info('Connected')
    minefield = socket.define(MinefieldNamespace, '/minefield')
    minefield.emit('new_game', nick)
    while socket.connected:
        socket.wait(seconds=1)
    logger.info('Disconnected')


def main():
    parser = argparse.ArgumentParser(description='Serve the Minefield Mahjong application.')
    parser.add_argument('--host', metavar='IP', type=str, default='127.0.0.1')
    parser.add_argument('--port', metavar='PORT', type=int, default=8080)
    parser.add_argument('--nick', metavar='NICK', type=str, default='Bot')
    args = parser.parse_args()

    init_logging()

    while True:
        bot_connect(args.host, args.port, args.nick)
        time.sleep(5)


if __name__ == '__main__':
    main()
