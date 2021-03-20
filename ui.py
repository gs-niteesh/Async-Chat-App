import urwid
import asyncio
from color_selector import ColorSelector
from client import connect_to_server, wait_for_data, send_msg_to_server

class UI:
    PALLETE = [
            ('header', 'black', 'white'),
            ('body', 'white', 'light gray')
            ]
    def __init__(self):
        self.message = []
        self.user = None
        self.loop = None
        for msg in self.message:
            msg = urwid.AttrMap(msg, 'body')

        self.header = urwid.Pile([urwid.AttrMap(urwid.Text('NIRC'), 'header'),
                                  urwid.Divider('-')])
        self.walker = urwid.SimpleListWalker(self.message)
        self.body = urwid.ListBox(self.walker)
        self.footer = urwid.Edit('> ')
        self.color = ColorSelector.get_color_attr()

        self.frame = urwid.Frame(body=self.body, header=self.header,
                                 footer=self.footer, focus_part='footer')
        urwid.connect_signal(self, 'update_msg_list', self.update_msg)

    def update_msg(self, org_msg):
        print ('update_smg')
        user, org_msg = org_msg.split(':')
        msg = [(self.color, user), ': ', org_msg]
        self.walker.append(urwid.Text(msg))

    async def run(self):
        await connect_to_server()
        self.loop.create_task(wait_for_data())

    def start(self):
        aloop = asyncio.get_event_loop()
        self.loop = aloop
        evl = urwid.AsyncioEventLoop(loop=aloop)
        loop = urwid.MainLoop(self.frame, UI.PALLETE, unhandled_input=self.handle_input, event_loop=evl)
        aloop.run_until_complete(self.run())
        loop.run()

    def handle_input(self, key):
        if key == 'f10':
            raise urwid.ExitMainLoop()
        if key == 'enter':
            org_msg = self.footer.get_edit_text()
            user = 'User Name:' # TODO
            msg = user + org_msg
            self.update_msg(msg)
            self.loop.create_task(send_msg_to_server(org_msg))
            self.footer.set_edit_text('')

    # async def send_msg_to_server(self, msg):
    #     print ('send_msg_to_server')
    #     writer.write(msg.encode())
    #     await writer.drain()

    # async def wait_for_data(self):
    #     global reader, writer
    #     while True:
    #         if reader is not None:
    #             data = await reader.read(100)
    #             urwid.emit_signal(self, 'update_msg_list', self, data)
    #         await asyncio.sleep(0)

    def set_cur_user(self, user):
        pass


    def update_msgs(self, msg):
        pass

if __name__ == '__main__':
    urwid.register_signal(UI, 'update_msg_list')

    UI().start()
