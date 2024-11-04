from functools import partial

from PySide6.QtWidgets import QWidget, QGridLayout
from PySide6.QtWidgets import QLabel, QComboBox, QPushButton
from PySide6.QtWidgets import QStyle, QCommonStyle
from PySide6.QtCore import Qt, Signal, QTimer

from ..dialogs.common import DataDialogWidget
from ..line_edit import LineEdit


UP_ICON = QStyle.SP_ArrowUp
DOWN_ICON = QStyle.SP_ArrowDown
DEL_ICON = QStyle.SP_TrashIcon


class TypeBox(QComboBox):
    user_types = ['hierarchy', 'single', 'multi']

    def __init__(self, value, read_only, update_cb):
        super().__init__()
        self.setEnabled(not read_only)
        self.addItems(self.user_types)
        if value not in self.user_types:
            self.addItem(value)
        self.setCurrentText(value)
        self.currentTextChanged.connect(update_cb)


class ActionButton(QPushButton):
    def __init__(self, icon, click_cb):
        super().__init__()
        self.setFocusPolicy(Qt.NoFocus)
        self.setIcon(QCommonStyle().standardIcon(icon))
        self.clicked.connect(click_cb)


class MetadataGrid(QWidget):
    def __init__(self, data, update_cb):
        super().__init__()
        self.data = data
        self.by_id = {entry['id']: entry for entry in self.data}
        assert len(self.by_id) == len(self.data) # IDs must be unique
        self.next_id = max(self.by_id) + 1
        self.update_cb = update_cb
        self.do_layout()

    def do_layout(self):
        QWidget().setLayout(self.layout()) # clears any existing layout
        self.setLayout(QGridLayout())
        for i, row in enumerate(self.make_grid()):
            for j, cell in enumerate(row):
                if cell:
                    self.layout().addWidget(cell, i, j)
        self.layout().setRowStretch(i + 1, 1)

    def refresh(self):
        # do_layout will destroy all existing widgets in the grid. This function
        # can be called from widget event callbacks so we delay do_layout until
        # after the callback has returned
        QTimer.singleShot(0, self.do_layout)
        self.update_cb(self.data)

    def new_cb(self):
        assert self.next_id not in self.by_id
        entry = {'name': self.new_box.text(), 'id': self.next_id, 'type': 'single',
                 'read_only': False}
        self.by_id[self.next_id] = entry
        self.data.append(entry)
        self.next_id += 1
        self.setFocus()
        self.refresh()

    def name_cb(self, entry_id, value):
        self.by_id[entry_id]['name'] = value # NOTE: also updates self.data
        self.update_cb(self.data)

    def type_cb(self, entry_id, value):
        self.by_id[entry_id]['type'] = value # NOTE: also updates self.data
        self.update_cb(self.data)

    def delete_cb(self, entry_id):
        entry = self.by_id.pop(entry_id)
        self.data.remove(entry)
        self.refresh()

    def reorder_cb(self, entry_id, offset):
        i = self.data.index(self.by_id[entry_id])
        j = i + offset
        self.data[i], self.data[j] = self.data[j], self.data[i]
        self.refresh()

    def make_grid(self):
        grid = [[QLabel("<b>%s</b>" % col) for col in ['Key', 'Type', 'Up', 'Dn', 'Del']]]
        is_first = True
        for i, entry in enumerate(self.data):
            is_last = i == len(self.data) - 1
            name = LineEdit(entry['name'], read_only=entry['read_only'],
                            update_cb=partial(self.name_cb, entry['id']))
            type_box = TypeBox(entry['type'], entry['read_only'],
                               update_cb=partial(self.type_cb, entry['id']))
            up = down = delete = None
            if not entry['read_only']:
                delete = ActionButton(DEL_ICON, partial(self.delete_cb, entry['id']))
                if not is_first:
                    up = ActionButton(UP_ICON, partial(self.reorder_cb, entry['id'], -1))
                if not is_last:
                    down = ActionButton(DOWN_ICON, partial(self.reorder_cb, entry['id'], 1))
                is_first = False
            grid.append([name, type_box, up, down, delete])

        self.new_box = LineEdit(commit_cb=self.new_cb)
        grid.append([QLabel("<b>Add new key<b>"), self.new_box])
        return grid


class MetadataEditorDialogWidget(DataDialogWidget):
    def __init__(self, data, update_cb, **kwargs):
        super().__init__(**kwargs)
        self.grid = MetadataGrid(data, update_cb)
        self.layout().addWidget(self.grid)
        self.add_action_buttons()
