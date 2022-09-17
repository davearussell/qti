from PySide6.QtWidgets import QWidget, QFrame, QScrollArea, QStackedLayout
from PySide6.QtWidgets import QLayout
from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt, Signal, Slot, QRect, QPoint, QSize

import keys


class FlowLayout(QLayout):
    def __init__(self, spacing=10, margin=10):
        super().__init__()
        self._margin = margin
        self._spacing = spacing
        self.items = []
        self.neighbours = {}

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        if 0 <= index < len(self.items):
            return self.items[index]

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        rect = QRect(0, 0, width, 0)
        return self.do_layout(rect, dry_run=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.do_layout(rect)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
        return size

    def do_layout(self, rect, dry_run=False):
        grid_left = x = rect.x() + self._margin
        y = rect.y() + self._margin
        grid_right = rect.right()
        row_height = 0
        rows = [[]]
        for item in self.items:
            item_width, item_height = item.sizeHint().toTuple()
            if row_height and x + item_width + self._margin > grid_right:
                x = grid_left
                y += row_height + self._spacing
                row_height = 0
                rows.append([])
            if not dry_run:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            rows[-1].append(item.widget())
            x += item_width + self._spacing
            row_height = max(row_height, item_height)

        if not dry_run:
            self.neighbours = {}
            for j, row in enumerate(rows):
                for i, cell in enumerate(row):
                    row_up = rows[(j - 1) % len(rows)]
                    row_down = rows[(j + 1) % len(rows)]
                    self.neighbours[cell] = {
                        'left': row[(i - 1) % len(row)],
                        'right': row[(i + 1) % len(row)],
                        'down': row_down[min(i, len(row_down) - 1)],
                        'up': row_up[min(i, len(row_up) - 1)],
                }
        return y + row_height - rect.y() + self._margin

    def scroll(self, widget, direction):
        return self.neighbours[widget][direction]


class Cell(QFrame):
    clicked = Signal(QFrame)
    double_clicked = Signal(QFrame)

    def __init__(self, widget):
        super().__init__()
        layout = QStackedLayout()
        self.setLayout(layout)
        layout.addWidget(widget)
        self.widget = widget
        self.setFocusPolicy(Qt.NoFocus)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)

    def enable_border(self, enabled):
        palette = self.palette()
        palette.setColor(QPalette.WindowText, Qt.yellow if enabled else Qt.black)
        self.setPalette(palette)

    def mousePressEvent(self, event):
        self.clicked.emit(self)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self)


class Grid(QScrollArea):
    target_selected = Signal(QWidget)
    unselected = Signal()
    target_updated = Signal(QWidget)
    spacing = 10

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setWidget(QWidget())
        self.target = None

    @Slot(QFrame)
    def set_target(self, cell):
        if self.target:
            self.target.enable_border(False)
        self.target = cell
        self.target.enable_border(True)
        self.target_updated.emit(self.target.widget)
        self.ensureWidgetVisible(cell)

    @Slot(QFrame)
    def select_target(self, cell):
        self.target_selected.emit(cell.widget)

    @Slot()
    def select_current_target(self):
        self.select_target(self.target)

    @Slot(str)
    def scroll(self, direction):
        cell = self.widget().layout().scroll(self.target, direction)
        self.set_target(cell)

    @Slot()
    def unselect(self):
        self.unselected.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.target:
            self.ensureWidgetVisible(self.target)

    def load(self, widgets, target=None):
        self.target = None
        if widgets and target is None:
            target = widgets[0]
        self.hide()
        QWidget().setLayout(self.widget().layout()) # clears our layout
        layout = FlowLayout(self.spacing)
        self.widget().setLayout(layout)

        for widget in widgets:
            cell = Cell(widget)
            cell.clicked.connect(self.set_target)
            cell.double_clicked.connect(self.select_target)
            layout.addWidget(cell)
            if widget is target:
                self.set_target(cell)
        self.show()

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        if action in ['up', 'down', 'left', 'right']:
            self.scroll(action)
        elif action == 'select':
            if self.target:
                self.select_current_target()
        elif action == 'unselect':
            self.unselect()
        else:
            event.ignore()
