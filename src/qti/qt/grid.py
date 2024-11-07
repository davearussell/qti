from PySide6.QtWidgets import QWidget, QFrame, QScrollBar, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import QPainter, QPen, QPalette

from .image import Image
from ..grid import Cell, layout_cells

class QCell(Cell):
    rect_cls = QRect
    image_cls = Image


class GridBody(QWidget):
    mouse_click = Signal(int, bool)
    height_updated = Signal(int)
    pos_updated = Signal(int)

    spacing = 10
    border_width = 2

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.NoFocus)
        self.pos = None
        self.cells = None
        self.grid_height = None
        self.grid = None
        self.target_i = None
        self.mark_i = None
        self.row_height = 0
        self.col_width = 0
        self.selected = QFrame()
        self.selected.setProperty('selectType', 'selected')
        self.marked = QFrame()
        self.marked.setProperty('selectType', 'marked')

    def set_pos(self, pos):
        if pos != self.pos:
            self.pos = pos
            self.pos_updated.emit(pos)
            self.repaint()

    def marked_range(self):
        try:
            if self.mark_i is None:
                mark_lo = mark_hi = self.target_i
            else:
                mark_lo = min(self.target_i, self.mark_i)
                mark_hi = max(self.target_i, self.mark_i)
        except ValueError:
            mark_lo = mark_hi = None
        return mark_lo, mark_hi

    @property
    def viewport(self):
        return QRect(0, self.pos, *self.size().toTuple())

    def load(self, cells):
        self.cells = cells #[self.renderer(self.settings, **cell_dict) for cell_dict in cell_dicts]
        self.pos = 0
        self.mark_i = None
        self.pos_updated.emit(0)
        if self.cells:
            cell_width, cell_height = self.cells[0].size
            self.row_height = cell_height + 2 * self.border_width + self.spacing
            self.col_width = cell_width + 2 * self.border_width + self.spacing
            self.setMinimumSize(QSize(self.col_width, self.row_height))
        self.setup_grid()

    def setup_grid(self):
        if self.cells:
            self.grid = layout_cells(self.cells, self.width(), self.cells[0].size,
                                     self.spacing, self.border_width)
            self.grid_height = self.cells[-1].spacing_rect.bottom()
        else:
            self.grid = []
            self.grid_height = 0
        self.height_updated.emit(self.grid_height)

    def ensure_visible(self, cell_i):
        cell = self.cells[cell_i]
        if cell.spacing_rect.bottom() > self.viewport.bottom(): # Need to scroll down
            self.set_pos(cell.spacing_rect.bottom() - self.viewport.height() + 1)
            return True
        elif cell.spacing_rect.top() < self.pos: # Need to scroll up
            self.set_pos(cell.spacing_rect.top())
            return True
        return False

    def handle_click(self, event, is_double):
        col, col_rem = divmod(event.pos().x(), self.col_width)
        row, row_rem = divmod(event.pos().y() + self.pos, self.row_height)
        if (col_rem >= self.spacing and # ignore clicks in the space between cells
            row_rem >= self.spacing and
            row < len(self.grid) and
            col < len(self.grid[row])):
            self.mouse_click.emit(self.grid[row][col].index, is_double)

    def mousePressEvent(self, event):
        self.handle_click(event, False)

    def mouseDoubleClickEvent(self, event):
        self.handle_click(event, True)

    def wheelEvent(self, event):
        new_pos = self.pos + self.row_height * (-1 if event.angleDelta().y() > 0 else 1)
        self.set_pos(max(min(new_pos, self.grid_height - self.height()), 0))

    def resizeEvent(self, event):
        self.setup_grid()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        mark_lo, mark_hi = self.marked_range()
        for i, cell in enumerate(self.cells):
            if cell.border_rect.intersects(self.viewport):
                pixmap = cell.contents()
                painter.drawPixmap(cell.contents_rect.translated(0, -self.pos), pixmap)
                if mark_lo <= i <= mark_hi:
                    tmp = (self.selected if i == self.target_i else self.marked)
                    pen = QPen(tmp.palette().color(QPalette.Text))
                    pen.setWidth(self.border_width)
                    pen.setJoinStyle(Qt.MiterJoin)
                    painter.setPen(pen)
                    painter.drawRect(cell.border_rect.translated(0, -self.pos))


class GridWidget(QFrame):
    renderer = QCell

    def __init__(self, app, click_cb):
        super().__init__()
        self.setObjectName("Grid")
        self.settings = app.settings
        self.click_cb = click_cb

        self.body = GridBody()
        self.body.mouse_click.connect(self.handle_click)
        self.body.height_updated.connect(self.body_height_update)
        self.body.pos_updated.connect(self.body_pos_update)

        self.scroll_bar = QScrollBar()
        self.scroll_bar.setMinimum(0)
        self.scroll_bar.valueChanged.connect(self.scroll_bar_moved)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.body)
        self.layout().addWidget(self.scroll_bar)

    def set_renderer(self, cls):
        self.renderer = cls

    def load(self, cell_dicts):
        cells = [self.renderer(self.settings, **cell_dict) for cell_dict in cell_dicts]
        self.body.load(cells)
        self.scroll_bar.setSingleStep(self.body.row_height)

    def set_target_i(self, i, ensure_visible=True):
        self.body.target_i = i
        repaint = True
        if ensure_visible and i is not None:
            repaint = not self.body.ensure_visible(i)
        if repaint:
            self.body.repaint()

    def set_mark_i(self, i):
        self.body.mark_i = i
        self.body.repaint()

    def cell_grid(self):
        return self.body.grid

    def handle_click(self, cell_i, is_double):
        self.click_cb(cell_i, is_double=is_double)

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
