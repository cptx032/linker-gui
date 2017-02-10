#!/usr/bin/env python
import string
from boring.window import Window
from boring.widgets import Entry, ScrollableExtendedListbox, Label, Button, Frame, SimpleCheckbox
import boring.dialog
import boring.form
from linker import models
import webbrowser

class NewElemWindow(boring.dialog.DefaultDialog):
    def __init__(self, master, initial=['', '']):
        self.output = None
        self.__initial = initial
        boring.dialog.DefaultDialog.__init__(self, master)

    def body(self, master):
        self.form = boring.form.FormFrame(
            master, 'Name@string\nDesc@string',
            initial_values=self.__initial
        )
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
        Window.__init__(self, bg='#dadada')
        self.__items = []
        self.___actual_item = 1
        self.title('Linker gui')

        self.__topframe = Frame(self)
        self.__topframe.configure(bg='#37474f')
        self.__topframe.pack(
            anchor='w', fill='x'
        )

        self.__folder_label = Label(
            self.__topframe,
            text='ok', fg='#ffffff',
            font=('TkDefaultFont', 12)
        )
        self.__folder_label.pack(
            anchor='w', side='left',
            pady=15,
            padx=15
        )

        self.commandentry = Entry(
            self.__topframe
        )
        self.commandentry.configure(
            bg='#c5c5c5', highlightthickness=0
        )
        self.commandentry.pack(
            pady=7, padx=8,
            fill='x', side='left', expand='yes'
        )

        self.close_check_box = SimpleCheckbox(self.__topframe, checked=True)
        self.close_check_box.pack(
            pady=7, padx=8,
            side='right'
        )
        Label(self.__topframe, text='Keep open', fg='#ffffff').pack(
            pady=7, padx=8,
            side='right'
        )

        self.commands = ScrollableExtendedListbox(
            self,
            width=800,
            height=300, highlightthickness=0,
            bd=0
        )
        self.commands.pack(
            expand='yes',
            fill='both',
            pady=0,
            padx=0
        )

        self.commandentry.focus_force()

        self.show_item(self.___actual_item)

        self.commandentry.bind('<Down>', lambda event: self.commands.down_selection(), '+')
        self.commandentry.bind('<Up>', lambda event: self.commands.up_selection(), '+')
        self.commandentry.bind('<Return>', self.__run_selected_command_handler, '+')
        self.bind('<Any-KeyRelease>', self.__key_handler, '+')
        self.bind('<Control-n>', self.__new_elem_handler, '+')

        self.bind('<Control-x>', self.__del_handler, '+')
        self.bind('<Control-e>', self.__edit_handler, '+')

        self.bind('<FocusIn>', lambda evt: self.commandentry.focus_force(), '+')

        self.protocol("WM_DELETE_WINDOW", self.__on_closing)

    def __on_closing(self):
        if not self.close_check_box.checked:
            self.destroy()

    def __edit_handler(self, event=None):
        selected = self.commands.get_selected()
        elem = models.Elem.search_by_name_description(
            selected.title, selected.subtitle
        )
        if elem:
            new = NewElemWindow(self, initial=[elem.name, elem.desc])
            if new.output:
                elem.name = new.output.get('name')
                elem.desc = new.output.get('desc')
                elem.update()
                parent = elem.get_parent()
                if parent:
                    self.show_item(parent.id)

    def __del_handler(self, event=None):
        selected = self.commands.get_selected()
        elem = models.Elem.search_by_name_description(
            selected.title, selected.subtitle
        )
        if elem and boring.dialog.OkCancel(self, u'Deseja excluir *%s*?' % elem.name).output:
            parent = elem.get_parent()
            elem.remove()
            self.show_item(parent.id)

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
        chars_that_do_refresh = list(string.printable)
        chars_that_do_refresh.extend(['BackSpace'])
        if event.keysym not in chars_that_do_refresh:
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

    def show_item(self, _id):
        elem = models.Elem.get_by_id(_id)
        if not elem:
            return

        if elem.type == models.LINK:
            webbrowser.open(elem.desc)
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
        self.commandentry.text = u''
        self.commandentry.focus_force()

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
