import asyncio
import random

class User:
    def __init__(self, addr, writer=None):
        self.name = 'random' + str(random.randrange(1000, 10000))
        self.addr = addr
        self.channel = ''
        self.writer = writer

    def set_channel(self, channel):
        self.channel = channel
        channels.setdefault(channel, []).append(self)

    async def send_msg(self, msg):
        msg = self.name + ': ' + msg
        self.writer.write(msg.encode())

    def connected(self):
        return self.channel != ''

users = []
channels = {}

def broadcast(msg):
    for user in users:
        user.writer.write(msg.encode())

def broadcast_in_channel(msg, cuser, channel):
    users = channels[channel]

    for user in users:
        if user != cuser:
            writer = user.writer
            writer.write(msg.encode())

def create_connect_user(addr, writer):
    user = User(addr, writer)
    users.append(user)
    broadcast(f'{user.name} Connected\n')
    return user

def disconnect_user(user):
    users.remove(user)
    print (f'{user.name} Disconnected')

async def handle(reader, writer):
    addr = writer.get_extra_info('peername')
    user = create_connect_user(addr, writer)
    while True:
        data = await reader.read(4096)
        if not data:
            disconnect_user(user)
            writer.close()
            return
        msg = data.decode()

        if not user.connected():
            if msg.startswith('/join'):
                channel = msg.split(' ')[1]
                channel = channel[:-2]
                user.set_channel(channel)
                broadcast_in_channel(f'{user.name} connected to channel {channel}\n', user, channel)
            elif msg.startswith('/name'):
                channel = msg.split(' ')[1]
                name = channel[:-2]
                broadcast_in_channel(f'{user.name} renamed to {name}', user, user.channel)
            else:
                writer.write('Connect to a channel first\n'.encode('ascii'))
        else:
            #TODO: Broadcast message to all users in the same channel
            broadcast_in_channel(msg, user, channel)
        await writer.drain()

async def main():
    server = await asyncio.start_server(
             handle, 'localhost', 8080)

    addr = server.sockets[0].getsockname()
    print(f'Servering on {addr}')

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main(), debug=True)
