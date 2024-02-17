from PySide6.QtWidgets import QWidget, QFrame, QScrollBar, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QRect, QEvent, QSize
from PySide6.QtGui import QPainter, QPen, QPixmap


class Cell:
    def __init__(self, size):
        self.size = size
        self.width = size.width()
        self.height = size.height()
        self.pixmap = None
        self.row = None
        self.col = None
        self.index = None
        self.border_rect = None
        self.pixmap_rect = None
        self.spacing_rect = None

    def load_pixmap(self):
        return QPixmap(self.width, self.height)

    def get_pixmap(self):
        if self.pixmap is None:
            self.pixmap = self.load_pixmap()
        return self.pixmap


class GridBody(QWidget):
    mouse_click = Signal(object, object)
    height_updated = Signal(int)
    pos_updated = Signal(int)

    spacing = 10
    border_width = 2

    def __init__(self, settings):
        super().__init__()
        self.setFocusPolicy(Qt.NoFocus)
        self.settings = settings
        self.pos = None
        self.cells = None
        self.grid_width = None
        self.grid_height = None
        self.grid = None
        self.target = None
        self.mark_i = None
        self.cell_width = None
        self.cell_height = None

    def set_pos(self, pos):
        if pos != self.pos:
            self.pos = pos
            self.pos_updated.emit(pos)
            self.repaint()

    def set_mark(self, _action=None):
        self.mark_i = self.cells.index(self.target)
        self.repaint()

    def clear_mark(self, _action=None):
        self.mark_i = None
        self.repaint()

    def marked_range(self):
        try:
            target_i = self.cells.index(self.target)
            if self.mark_i is None:
                mark_lo = mark_hi = target_i
            else:
                mark_lo = min(target_i, self.mark_i)
                mark_hi = max(target_i, self.mark_i)
        except ValueError:
            mark_lo = mark_hi = target_i = None
        return mark_lo, mark_hi, target_i

    @property
    def viewport(self):
        return QRect(0, self.pos, *self.size().toTuple())

    def load(self, cells):
        self.cells = cells
        self.pos = 0
        self.mark_i = None
        self.pos_updated.emit(0)
        if cells:
            self.cell_width = cells[0].width
            self.cell_height = cells[0].height
            self.row_height = self.cell_height + 2 * self.border_width + self.spacing
            self.col_width = self.cell_width + 2 * self.border_width + self.spacing
            self.setMinimumSize(QSize(self.col_width, self.row_height))
        self.setup_grid()

    def setup_grid(self):
        self.grid_width = self.width()
        self.grid = []
        if self.cells:
            n_cols = max(1, (self.grid_width - self.spacing) // self.col_width)
            for i, cell in enumerate(self.cells):
                cell.index = i
                cell.row, cell.col = divmod(i, n_cols)
                if cell.row >= len(self.grid):
                    self.grid.append([])
                assert len(self.grid[cell.row]) == cell.col, (cell.row, cell.col)
                self.grid[cell.row].append(cell)
                cell_x = self.spacing + cell.col * self.col_width
                cell_y = self.spacing + cell.row * self.row_height - self.pos
                cell.border_rect = QRect(cell_x, cell_y,
                                         self.col_width - self.spacing,
                                         self.row_height - self.spacing)
                cell.pixmap_rect = QRect(cell_x + self.border_width, cell_y + self.border_width,
                                         self.cell_width, self.cell_height)
                cell.spacing_rect = QRect(cell_x - self.spacing, cell_y - self.spacing,
                                          self.col_width + self.spacing,
                                          self.row_height + self.spacing)
            self.grid_height = self.cells[-1].spacing_rect.bottom()
        else:
            self.grid_height = 0
        self.height_updated.emit(self.grid_height)

    def ensure_visible(self, cell):
        if cell.spacing_rect.bottom() > self.viewport.bottom(): # Need to scroll down
            self.set_pos(cell.spacing_rect.bottom() - self.viewport.height() + 1)
            return True
        elif cell.spacing_rect.top() < self.pos: # Need to scroll up
            self.set_pos(cell.spacing_rect.top())
            return True
        return False

    def handle_click(self, event):
        col, col_rem = divmod(event.pos().x(), self.col_width)
        row, row_rem = divmod(event.pos().y() + self.pos, self.row_height)
        if (col_rem >= self.spacing and # ignore clicks in the space between cells
            row_rem >= self.spacing and
            row < len(self.grid) and
            col < len(self.grid[row])):
            self.mouse_click.emit(self.grid[row][col], event.type())

    def mousePressEvent(self, event):
        self.handle_click(event)

    def mouseDoubleClickEvent(self, event):
        self.handle_click(event)

    def wheelEvent(self, event):
        new_pos = self.pos + self.row_height * (-1 if event.angleDelta().y() > 0 else 1)
        self.set_pos(max(min(new_pos, self.grid_height - self.height()), 0))

    def resizeEvent(self, event):
        self.setup_grid()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        mark_lo, mark_hi, target_i = self.marked_range()
        for i, cell in enumerate(self.cells):
            if cell.border_rect.intersects(self.viewport):
                painter.drawPixmap(cell.pixmap_rect.translated(0, -self.pos), cell.get_pixmap())
                if mark_lo <= i <= mark_hi:
                    color = 'selection_color' if i == target_i else 'mark_color'
                    pen = QPen(self.settings.get(color))
                    pen.setWidth(self.border_width)
                    pen.setJoinStyle(Qt.MiterJoin)
                    painter.setPen(pen)
                    painter.drawRect(cell.border_rect.translated(0, -self.pos))


class Grid(QFrame):
    target_selected = Signal(object)
    unselected = Signal()
    target_updated = Signal(object)

    def __init__(self, settings, keybinds):
        super().__init__()
        self.keybinds = keybinds
        self.setObjectName("Grid")

        self.body = GridBody(settings)
        self.body.mouse_click.connect(self.handle_click)
        self.body.height_updated.connect(self.body_height_update)
        self.body.pos_updated.connect(self.body_pos_update)

        self.scroll_bar = QScrollBar()
        self.scroll_bar.setMinimum(0)
        self.scroll_bar.valueChanged.connect(self.scroll_bar_moved)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.body)
        self.layout().addWidget(self.scroll_bar)

        self.action_map = {
            'up': self.scroll,
            'down': self.scroll,
            'left': self.scroll,
            'right': self.scroll,
            'top': self.scroll,
            'bottom': self.scroll,
            'select': self.select_current_target,
            'unselect': self.unselect,
            'mark': self.body.set_mark,
            'cancel': self.body.clear_mark,
        }

    @property
    def target(self):
        return self.body.target

    def marked_cells(self):
        lo, hi, _ = self.body.marked_range()
        if lo is None:
            return []
        return self.body.cells[lo : hi + 1]

    def load(self, cells, target):
        self.body.load(cells)
        self.scroll_bar.setSingleStep(self.body.row_height)
        self.set_target(target)

    def set_target(self, cell, ensure_visible=True):
        self.body.target = cell
        redrawn = cell and ensure_visible and self.body.ensure_visible(cell)
        if not redrawn:
            self.body.repaint()
        self.target_updated.emit(cell)

    def unselect(self, _action=None):
        self.unselected.emit()

    def select_target(self, cell):
        self.target_selected.emit(cell)

    def select_current_target(self, _action=None):
        if self.target:
            self.select_target(self.target)

    def body_height_update(self, height):
        if height <= self.body.height():
            self.scroll_bar.setMaximum(0)
            self.scroll_bar.hide()
        else:
            self.scroll_bar.show()
            self.scroll_bar.setMaximum(height - self.body.height())
            self.scroll_bar.setPageStep(self.body.height())

    def body_pos_update(self, pos):
        self.scroll_bar.setValue(pos)

    def scroll_bar_moved(self, value):
        self.body.set_pos(value)

    def handle_click(self, cell, click_type):
        if click_type == QEvent.MouseButtonPress:
            self.set_target(cell, ensure_visible=False)
        elif click_type == QEvent.MouseButtonDblClick:
            self.select_target(cell)

    def neighbour(self, cell, direction):
        row, col = cell.row, cell.col
        if direction in ('left', 'right'):
            offset = (1 if direction == 'right' else -1)
            col = (col + offset) % len(self.body.grid[row])
        elif direction in ('up', 'down'):
            offset = (1 if direction == 'down' else -1)
            row = (row + offset) % len(self.body.grid)
            if col >= len(self.body.grid[row]):
                col = len(self.body.grid[row]) - 1
        elif direction in ('top', 'bottom'):
            row = col = (0 if direction == 'top' else -1)
        return self.body.grid[row][col]

    def scroll(self, direction):
        if self.target:
            self.set_target(self.neighbour(self.target, direction))

    def keyPressEvent(self, event):
        action = self.keybinds.get_action(event)
        if action in self.action_map:
            self.action_map[action](action)
        else:
            event.ignore()
