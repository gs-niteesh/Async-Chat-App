from enum import Enum

import asyncio
import random
import json
import logging

logging.basicConfig(level=logging.INFO)

class User:
    def __init__(self, addr, writer=None):
        self.name = 'random' + str(random.randrange(1000, 10000))
        self.addr = addr
        self.channel = ''
        self.writer = writer

    async def send_msg(self, msg):
        self.writer.write(msg.encode())
        await self.writer.drain()

    def connected(self):
        return self.channel != ''

def send_event_msg(msg):
    return json.dumps({'type': 'event', 'msg': msg})

def send_user_msg(msg, user):
    return json.dumps({'type': 'msg', 'user': user.name, 'msg': msg})

def send_name_msg(user):
    return json.dumps({'type': 'name', 'name': user.name})

users = []
channels = {}

async def broadcast(msg, c_user):
    msg = send_event_msg(msg)
    for user in users:
        if user != c_user:
            await user.send_msg(msg)

async def broadcast_in_channel(msg, c_user, channel, is_event = False):
    smsg = send_event_msg(msg)
    if not is_event:
        smsg = send_user_msg(msg, c_user)

    users = channels.get(channel, [])
    for user in users:
        if user != c_user:
            await user.send_msg(smsg)

async def create_connect_user(addr, writer):
    user = User(addr, writer)
    users.append(user)

    # Send the name allocated by the server to the user.
    # This name can later be changed using /name command.
    msg = send_name_msg(user)
    await user.send_msg(msg)

    await broadcast(f'{user.name} Connected\n', user)
    return user

def disconnect_user(user):
    # Remove the user from the users list and channel list
    channel = user.channel
    assert user != None
    assert user != ''
    users.remove(user)
    if user.connected():
        channels[channel].remove(user)
    user.writer.close()
    # FIXME: Change to broadcast
    logging.info(f'{user.name} Disconnected')

class MsgType(Enum):
    UNKNOWN = 0
    JOIN = 1
    NAME = 2
    MESG = 3

def parse_msg_type(msg):
    # Messages starting with / are commands to the server
    # /join <channel> - Joins the user the channel
    # /name <name> - Renames the user to name
    msg.strip(' \n\r')

    if not msg.startswith('/'):
        return (MsgType.MESG, msg)

    [cmd, val] = msg.split(' ')
    if cmd == '/join':
        return (MsgType.JOIN, val)
    elif cmd == '/name':
        return (MsgType.NAME, val)

    return (MsgType.UNKNOWN, msg)

async def handle_join_msg(channel, user):
    old_channel = user.channel

    if user.connected():
        logging.info(f'${user.name} changed to channel ${channel}')
        channels[old_channel].remove(user)
        await broadcast_in_channel(f'${user.name} disconnected from channel ${user.channel}')
    else:
        logging.info(f'Connecting ${user.name} to channel ${channel}')
        await broadcast_in_channel(f'{user.name} connected to channel {channel}\n', user, channel, is_event=True)

    # Add user to new channel
    user.channel = channel
    channels.setdefault(channel, []).append(user)

async def handle_name_msg(msg, user):
    user.name = name
    await broadcast_in_channel(f'{user.name} renamed to {name}', user, user.channel, is_event=True)

async def handle_user_msg(msg, user):
    if not user.connected():
        msg = send_event_msg('Connect to a channel first\n')
        await user.send_msg(msg)
    else:
        logging.info(f'broadcasting ${msg} in channel ${user.channel}')
        await broadcast_in_channel(msg, user, user.channel)

async def handle(reader, writer):
    # Create the user object and broadcast about the user to other users.
    addr = writer.get_extra_info('peername')
    logging.info(f'User with addr {addr} connected\n')
    user = await create_connect_user(addr, writer)

    while True:
        data = await reader.read(4096)
        if not data:
            disconnect_user(user)
            return
        msg = data.decode()
        logging.debug(f'received ${msg} from ${user.name}')

        (msg_type, val) = parse_msg_type(msg)
        if msg_type == MsgType.JOIN:
            await handle_join_msg(val, user)
        elif msg_type == MsgType.NAME:
            await handle_name_msg(val, user)
        elif msg_type == MsgType.MESG:
            await handle_user_msg(val, user)

async def main():
    server = await asyncio.start_server(handle, 'localhost', 8080)

    addr = server.sockets[0].getsockname()
    logging.info(f'Servering on {addr}')

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main(), debug=True)
