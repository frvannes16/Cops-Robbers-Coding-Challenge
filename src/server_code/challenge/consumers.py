from challenge.models import Game

from channels import Group
from channels.sessions import channel_session

import logging
import re

log = logging.getLogger(__name__)
@channel_session
def ws_connect(message):
    log.info('Connect')
    # Accept the incoming connection
    path = message['path']
    pattern = re.compile(r'challenge/game/(?P<a>[^/]+)/(?P<b>[^/]+)/')
    match = re.search(pattern, path)
    if match:
        a_team = match.group('a')
        b_team = match.group('b')
        game = Game.get_game(a_team, b_team)
        message.reply_channel.send({'accept': True})
        # Add them to the Group
        Group(game.get_group_key()).add(message.reply_channel)
    else:
        log.debug("Consumer doesn't recognize url: " + path)  # Do nothing if the url isn't recognized.

@channel_session
def ws_receive(message):
    log.debug('Receive')
    message.reply_channel.send({
        'text': message.content['text'],
    })

@channel_session
def ws_disconnect(message):
    log.debug('Disconnect')
    path = message['path']
    pattern = re.compile(r'challenge/game/(?P<a>[^/]+)/(?P<b>[^/]+)/')
    match = re.search(pattern, path)
    if match:
        a_team = match.group('a')
        b_team = match.group('b')
        game = Game.get_game(a_team, b_team, active_matters=False)
        message.reply_channel.send({'accept': True})
        Group(game.get_group_key()).discard(message.reply_channel)
    else:
        log.debug("Consumer doesn't recognize url: " + path)
