import asyncio
import logging
import sys

reader = None
writer = None
connected = False

logging.basicConfig(
                level=logging.DEBUG,
                format='%(levelname)7s: %(message)s',
                stream=sys.stderr,
            )
LOG = logging.getLogger('')
loop = None

async def send_msg_to_server(msg):
    print ('send_msg_to_server')
    global writer
    writer.write(msg.encode())
    await writer.drain()

async def wait_for_data():
    global reader
    while True:
        if reader is not None:
            data = await reader.read(100)
            print (data.decode())
        await asyncio.sleep(0)

async def connect_to_server():
    global reader, writer, connected
    if not connected:
        reader, writer = await asyncio.open_connection('localhost', 8080)
        connected = True

async def main():
    await connect_to_server()
    asyncio.create_task(wait_for_data())

if __name__ == '__main__':
    #print ('Running')
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(main())
    loop.run_forever()
    loop.close()
