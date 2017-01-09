#!/usr/bin/env python
from boring.window import Window
from boring.widgets import Entry, ScrollableExtendedListbox, Label
import boring.dialog
import boring.form
from linker import models

class NewElemWindow(boring.dialog.DefaultDialog):
    def __init__(self, master):
        self.output = None
        boring.dialog.DefaultDialog.__init__(self, master)

    def body(self, master):
        self.form = boring.form.FormFrame(
            master, 'Name@string\nDesc@string')
        self.form.grid(pady=10, padx=10)

        return self.form.inputs[0]

    def validate(self):
        return all(self.form.values)

    def apply(self):
        self.output = {
            'name': self.form.values[0],
            'desc': self.form.values[1]
        }

class MainWindow(Window):
    def __init__(self):
        Window.__init__(self)
        self.__items = []
        self.___actual_item = 1
        self.title('Linker gui')

        self.__folder_label = Label(self, text='ok')
        self.__folder_label.pack(
            anchor='w',
            pady=5,
            padx=5
        )

        self.commandentry = Entry(self)
        self.commandentry.pack(
            pady=5, padx=5,
            fill='x'
        )

        self.commands = ScrollableExtendedListbox(
            self,
            width=800,
            height=300, highlightthickness=0
        )
        self.commands.pack(
            expand='yes',
            fill='both',
            pady=0,
            padx=5
        )

        self.commandentry.focus_force()

        self.show_item(self.___actual_item)

        self.commandentry.bind('<Down>', lambda event: self.commands.down_selection(), '+')
        self.commandentry.bind('<Up>', lambda event: self.commands.up_selection(), '+')
        self.commandentry.bind('<Return>', self.__run_selected_command_handler, '+')
        self.bind('<Any-KeyRelease>', self.__key_handler, '+')
        self.bind('<Control-n>', self.__new_elem_handler, '+')

    def __new_elem_handler(self, event=None):
        new = NewElemWindow(self)
        if new.output:
            t = models.FOLDER
            if new.output.get('desc').startswith('http'):
                t = models.LINK
            m = models.Elem(None,
                new.output.get('name'),
                t, new.output.get('desc'),
                self.___actual_item
            )
            models.Elem.insert(m)
            self.show_item(self.___actual_item)

    def __key_handler(self, event):
        if event.keysym in ('Up', 'Down', 'Return', 'Escape'):
            return
        final_items = []
        entry_text = self.commandentry.text.lower()

        for menu in self.__items:
            menu_title = menu.get('name').lower()

            if entry_text in menu_title:
                final_items.append(menu)

        self.show_items(final_items)

    def __run_selected_command_handler(self, event=None):
        selected = self.commands.get_selected()
        if selected:
            selected.before_click(None)
            self.commandentry.text = ''

    def show_item(self, _id):
        elem = models.Elem.get_by_id(_id)
        if not elem:
            return
        self.___actual_item = _id
        self.__folder_label.text = elem.name
        items = list()

        parent = elem.get_parent()
        if parent:
            items.append({
                'name': '...',
                'subtitle': 'back a folder',
                'command': self.__create_item_click_handler(parent.id)
            })
        for i in elem.get_elems():
            item_dict = dict(
                icon=None,
                name=i.name,
                subtitle=i.desc,
                command=self.__create_item_click_handler(i.id)
            )
            if i.type == models.FOLDER:
                item_dict['icon'] =  'icons/folder.png'
            elif i.type == models.LINK:
                item_dict['icon'] = 'icons/note.png'
            items.append(item_dict)
        self.items = items
        self.show_items(items)

    def __create_item_click_handler(self, _id):
        def __handler(event=None):
            self.show_item(_id)
        return __handler

    @property
    def items(self):
        return self.__items

    @items.setter
    def items(self, value):
        self.__items = value

    def show_items(self, items):
        self.commands.delete_all()
        self.add_items(items)
        self.commands.select_first()

    def add_items(self, items):
        for i in items:
            self.commands.add_item(
                i.get('name'),
                before_click=self.__item_click_handler(
                    i.get('command', None)
                ),
                subtitle=i.get('subtitle', None),
                icon=i.get('icon', None)
            )

    def __item_click_handler(self, function):
        def __final_function(*args):
            if function:
                function(*args)
        return __final_function

if __name__ == '__main__':
    top = MainWindow()
    top.center()
    top.mainloop()