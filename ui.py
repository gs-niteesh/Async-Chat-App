import urwid
import asyncio
from color_selector import ColorSelector
import json
import logging
import sys
import traceback

logging.basicConfig(filename='ui.log', level=logging.DEBUG)

reader = None
writer = None
connected = False

class SclackEventLoop(urwid.AsyncioEventLoop):
    def run(self):
        self._loop.set_exception_handler(self._custom_exception_handler)
        self._loop.run_forever()
    def set_exception_handler(self, handler):
        self._custom_exception_handler = handler

async def send_msg_to_server(msg):
    global writer
    writer.write(msg.encode())
    await writer.drain()

async def connect_to_server():
    global reader, writer, connected
    if not connected:
        reader, writer = await asyncio.open_connection('localhost', 8080)
        connected = True

class UI:
    PALLETE = [
            ('header', 'black', 'white'),
            ('body', 'white', 'light gray')
            ]
    def __init__(self):
        self.message = []
        self.user = None
        self.loop = None
        self.user_name = '????'
        for msg in self.message:
            msg = urwid.AttrMap(msg, 'body')

        self.header = urwid.Pile([urwid.AttrMap(urwid.Text('NIRC'), 'header'),
                                  urwid.Divider('-')])
        self.walker = urwid.SimpleListWalker(self.message)
        self.body = urwid.ListBox(self.walker)
        self.footer = urwid.Edit('> ', multiline=True, allow_tab=True)
        self.color = ColorSelector.get_color_attr()

        self.frame = urwid.Frame(body=self.body, header=self.header,
                                 footer=self.footer, focus_part='footer')
        urwid.connect_signal(self, 'update_msg_list', self.update_msg)


    def _exception_handler(self, loop, context):
        try:
            exception = context.get('exception')
            if not exception:
                raise Exception
            message = 'Whoops, something went wrong:\n\n' + str(exception) + \
                      '\n' + ''.join(traceback.format_tb(exception.__traceback__))
            logging.debug(message)
            self.walker.append(urwid.Text(message))
        except Exception as exc:
            logging.debug('Unable to show exception: ' + str(exc))
            self.walker.append(urwid.Text('Unable to show exception: ' + str(exc)))
        return

    def update_msg(self, user, org_msg):
        attr = urwid.AttrSpec('default', 'dark red'),
        msg = [(attr, user), ': ', org_msg]
        self.walker.append(urwid.Text(msg))

    async def run(self):
        await connect_to_server()
        self.loop.create_task(self.wait_for_data())

    def start(self):
        global writer
        aloop = asyncio.get_event_loop()
        self.loop = aloop
        #evl = SclackEventLoop(loop=aloop)
        #evl.set_exception_handler(self._exception_handler)
        evl = urwid.AsyncioEventLoop(loop=aloop)
        loop = urwid.MainLoop(self.frame, UI.PALLETE,
                              unhandled_input=self.handle_input, event_loop=evl)
        aloop.run_until_complete(self.run())
        loop.run()
        writer.close()
        aloop.close()

    def handle_input(self, key):
        if key == 'f10':
            raise urwid.ExitMainLoop()
        if key == 'enter':
            org_msg = self.footer.get_edit_text()
            if not org_msg.startswith('/'):
                self.update_msg(self.user_name, org_msg)
                pass
            self.loop.create_task(send_msg_to_server(org_msg))
            self.footer.set_edit_text('')

    async def wait_for_data(self):
        global reader
        while True:
            if reader is not None:
                data = await reader.read(4096)
                if data:
                    msg = data.decode()
                    # urwid.emit_signal(self, 'update_msg_list', self, data)
                    # print ('data: ', msg, type(msg))
                    try:
                        data = json.loads(msg)
                    except json.JSONDecodeError:
                        logging.debug(msg)
                        data = {'type':'msg', 'user': 'anon', 'msg': 'Fix me'}
                    
                    # data = self.return_dict(msg)
                    logging.debug(msg)
                    typ = data.get('type')
                    msg = data.get('msg')
                    name = data.get('name')
                    user = data.get('user')
                    if typ == None:
                        logging.debug('Data event type is none' + data)
                        continue
                    if typ == 'event':
                         self.walker.append(urwid.Text(msg))
                    elif typ == 'name':
                        self.user_name = name
                        self.walker.append(urwid.Text('Name: ' + self.user_name))
                    else:
                        logging.debug(f'message from ${user} msg: ${msg}')
                        msg = user + ': ' + msg
                        logging.debug(f'${msg} to pushed to list')
                        self.walker.append(urwid.Text(msg))

            await asyncio.sleep(0)

if __name__ == '__main__':
    urwid.register_signal(UI, 'update_msg_list')

    UI().start()
