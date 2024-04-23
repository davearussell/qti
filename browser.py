from grid import Grid, Cell
from viewer import Viewer
from pathbar import Pathbar
from tree import TreeError

from qt.browser import BrowserWidget, NodeRenderer


class NodeCell(Cell):
    def __init__(self, node, settings):
        self.node = node
        count = len(node.children)
        image = next(node.images()) if count else node
        label = node.name if count else None
        renderer = NodeRenderer(settings, image, label, count)
        super().__init__(renderer, label)


class Browser:
    def __init__(self, app):
        self.app = app
        self.library = self.app.library
        self.keybinds = app.keybinds
        self.mode = None
        self.node = None
        self.target = None
        self.hide_bars = False
        self.setup_widgets()

    def setup_widgets(self):
        self.grid = Grid(scroll_cb=self._target_updated,
                         select_cb=self.select,
                         unselect_cb=self.unselect)
        self.viewer = Viewer(self.app,
                             scroll_cb=self._target_updated,
                             close_cb=self.unselect)
        self.pathbar = Pathbar(click_cb=self.unselect)
        self.ui = BrowserWidget(grid=self.grid.ui,
                                viewer=self.viewer.ui,
                                status_bar=self.app.status_bar.ui,
                                pathbar=self.pathbar.ui,
                                keydown_cb=self.handle_keydown)

    def _target_updated(self, target):
        if isinstance(target, NodeCell):
            target = target.node
        self.pathbar.set_target(target)
        self.target = target

    def set_mode(self, mode):
        if mode is None:
            mode = self.mode or 'grid'
        if mode != self.mode:
            self.mode = mode
            self.ui.set_mode(mode)

    def load_node(self, node, target=None, mode=None):
        self.node = node
        self.target = target or (node.children[0] if node.children else None)
        self.set_mode(mode)
        if self.mode == 'grid':
            self.pathbar.fade_target = True
            thumbs = [NodeCell(child, self.app.settings) for child in self.node.children]
            tthumb = thumbs[self.node.children.index(self.target)] if self.target else None
            self.grid.load(thumbs, target=tthumb)
        else:
            self.pathbar.fade_target = False
            self.viewer.load(self.node, self.target)

    def reload_node(self):
        if self.node:
            self.load_node(self.node, self.target, self.mode)

    def select(self, widget):
        assert isinstance(widget, NodeCell), widget
        target = widget.node
        if target.children:
            self.load_node(target, mode='grid')
        else:
            self.load_node(target.parent, target=target, mode='viewer')

    def unselect(self, node=None):
        if node is None:
            node = self.node
        if node.parent:
            self.load_node(node.parent, target=node, mode='grid')

    def scroll_node(self, action):
        if not self.node.parent:
            return
        siblings = self.node.parent.children
        offset = {'up': -1, 'prev': -1, 'down': 1, 'next': 1}[action]
        new_node = siblings[(siblings.index(self.node) + offset) % len(siblings)]
        self.load_node(new_node)

    def scroll(self, action):
        widget = self.grid if self.mode == 'grid' else self.viewer
        if action in widget.action_map:
            widget.action_map[action](action)
        else:
            self.scroll_node(action)

    def swap_cells(self, direction):
        cells = self.node.children
        if direction in ['left', 'right']:
            i = (self.target.index + (1 if direction == 'right' else -1)) % len(cells)
            other = cells[i]
        elif self.mode == 'grid':
            other = self.grid.neighbour(self.grid.target, direction).node
        else:
            return # Cannot swap verticaly when in viewer mode

        try:
            self.target.swap_with(other)
            self.load_node(self.node, self.target)
        except TreeError as e:
            self.app.status_bar.set_text("Cannot swap (%s)" % e, duration_s=5)

    def marked_nodes(self):
        if self.mode == 'grid':
            return [cell.node for cell in self.grid.marked_cells()]
        return [self.target]

    def handle_keydown(self, keystroke):
        action = self.keybinds.get_action(keystroke)
        widget = self.viewer if self.mode == 'viewer' else self.grid
        if widget.handle_action(action):
            pass
        elif action in ['prev', 'next', 'up', 'down']:
            # NOTE: up/down here is only reachable in viewer mode; in grid
            # mode the grid class consumes them to scroll with in the grid
            self.scroll_node(action)
        elif action in ['swap_up', 'swap_down', 'swap_left', 'swap_right']:
            self.swap_cells(action[len('swap_'):])
        elif action == 'toggle_hide':
            self.hide_bars = not self.hide_bars
            self.ui.set_bar_visibility(self.hide_bars)
        else:
            return False
        return True
