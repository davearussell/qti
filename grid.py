from PySide6.QtWidgets import QWidget, QFrame, QScrollArea, QStackedLayout
from PySide6.QtWidgets import QLayout
from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt, Signal, Slot, QRect, QPoint, QSize


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
                        Qt.Key_Left: row[(i - 1) % len(row)],
                        Qt.Key_Right: row[(i + 1) % len(row)],
                        Qt.Key_Down: row_down[min(i, len(row_down) - 1)],
                        Qt.Key_Up: row_up[min(i, len(row_up) - 1)],
                }
        return y + row_height - rect.y() + self._margin

    def scroll(self, widget, direction):
        return self.neighbours[widget][direction]


class Cell(QFrame):
    focused = Signal(QFrame)
    selected = Signal(QFrame)

    def __init__(self, widget):
        super().__init__()
        layout = QStackedLayout()
        self.setLayout(layout)
        layout.addWidget(widget)
        self.widget = widget
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)

    def set_border_color(self, color):
        palette = self.palette()
        palette.setColor(QPalette.WindowText, color)
        self.setPalette(palette)

    def focusInEvent(self, event):
        self.set_border_color(Qt.yellow)
        self.focused.emit(self)

    def focusOutEvent(self, event):
        self.set_border_color(Qt.black)

    def mouseDoubleClickEvent(self, event):
        self.selected.emit(self)


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
    def cell_focused(self, cell):
        self.target = cell
        self.target_updated.emit(self.target.widget)

    @Slot(QFrame)
    def cell_selected(self, cell):
        self.target = cell
        self.target_selected.emit(self.target.widget)

    def resizeEvent(self, event):
        if self.target:
            self.ensureWidgetVisible(self.target)

    def set_target(self, cell):
        self.target = cell
        cell.setFocus()
        self.ensureWidgetVisible(cell)

    def load(self, widgets, target=None):
        self.hide()
        QWidget().setLayout(self.widget().layout()) # clears our layout
        layout = FlowLayout(self.spacing)
        self.widget().setLayout(layout)

        for widget in widgets:
            cell = Cell(widget)
            cell.focused.connect(self.cell_focused)
            cell.selected.connect(self.cell_selected)
            layout.addWidget(cell)
            if widget is target:
                self.set_target(cell)
        self.show()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.target:
            self.target.setFocus()

    def keyPressEvent(self, event):
        key = event.key()
        if key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right]:
            self.set_target(self.widget().layout().scroll(self.target, key))
        elif key == Qt.Key_Return:
            if self.target:
                self.target_selected.emit(self.target.widget)
        elif key == Qt.Key_Backspace:
            self.unselected.emit()
        else:
            event.ignore()
