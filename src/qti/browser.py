import pygame

from xui.widgets import VBox, VSpacer, ScrollArea

from .grid import Grid, Thumbnail
from .viewer import Viewer
from .pathbar import Pathbar
from .status_bar import StatusBar

# TODO:
#  * Marking


class Browser(VBox):
    name_size = 14
    count_size = 30

    def __init__(self):
        super().__init__()
        self.library = self.app.library
        self.keybinds = self.app.keybinds
        self.mode = None
        self.node = None
        self.hide_bars = False
        self.grid = Grid(click_cb=self._grid_click)
        self.grid_scroller = ScrollArea(self.grid, greedy_height=True, right_bar=True)
        self.viewer = Viewer()
        self.pathbar = Pathbar(click_cb=self._pathbar_click)
        self.status_bar = StatusBar()
        self.overlay = VBox([self.pathbar, VSpacer(), self.status_bar], bgcolor=(0, 0, 0, 0))

    def settings_updated(self):
        self.setup_widgets()

    def _grid_click(self, cell_i, is_double):
        self._set_target_i(cell_i)
        if is_double:
            self.select()

    def _pathbar_click(self, node):
        self.load_node(node.parent, target=node, mode='grid')

    def setup_grid(self):
        if self.hide_bars:
            self.children = [self.grid_scroller]
        else:
            self.children = [self.pathbar, self.grid_scroller, self.status_bar]
        self.pathbar.bgcolor = pygame.Color(self.screen.bgcolor).lerp('black', 0.5)
        self.status_bar.bgcolor = pygame.Color(self.screen.bgcolor).lerp('black', 0.5)

    def setup_viewer(self):
        self.children = [self.viewer]
        if not self.hide_bars:
            self.pathbar.bgcolor = (0, 0, 0, 128)
            self.status_bar.bgcolor = (0, 0, 0, 128)
            self.screen.children.insert(1, self.overlay)

    def setup_widgets(self):
        if self.overlay in self.screen.children:
            self.screen.children.remove(self.overlay)
        if self.mode == 'grid':
            self.setup_grid()
        else:
            self.setup_viewer()
        self.pathbar.set_target(self.get_target(), fade=self.mode == 'grid')
        self.relayout()
        self.redraw()

    def set_mode(self, mode):
        if mode is None:
            mode = self.mode or 'grid'
        if mode != self.mode:
            self.mode = mode
            self.setup_widgets()

    def toggle_hide(self):
        self.hide_bars = not self.hide_bars
        self.setup_widgets()

    def get_target(self):
        if not self.node.children:
            return None
        return self.node.children[self.grid.get_target_i()]

    def set_target(self, target):
        if target.parent == self.node:
            self._set_target_i(self.node.children.index(target))
        else:
            self.load_node(target.parent, target, self.mode)

    def load_node(self, node, target=None, mode=None):
        if node.children and not target:
            target = node.children[0]
        self.node = node
        self.grid.load_cells([Thumbnail(self, child) for child in node.children])
        target_i = node.children.index(target) if node.children else None
        self._set_target_i(target_i)
        self.set_mode(mode)

    def reload_node(self):
        if self.node:
            self.load_node(self.node, self.get_target(), self.mode)

    def marked_nodes(self):
        pass # XXX  "Write me!"

    def delete_nodes(self, nodes, propagate=None):
        old_parent = nodes[0].parent
        root = old_parent.root
        for node in nodes:
            new_target = node.delete(propagate=propagate)
        new_parent = root if new_target is None else new_target.parent
        mode = 'grid' if new_parent != old_parent else self.mode
        self.load_node(new_parent, target=new_target, mode=mode)

    def scroll_node(self, forwards):
        if not self.node.parent:
            return
        siblings = self.node.parent.children
        i = (siblings.index(self.node) + (1 if forwards else -1)) % len(siblings)
        self.load_node(siblings[i])

    def _set_target_i(self, target_i):
        target = None if target_i is None else self.node.children[target_i]
        self.pathbar.set_target(target, fade=self.mode == 'grid')
        self.grid.set_target_i(target_i)
        if target and self.mode == 'viewer':
            self.viewer.load(target.abspath)

    def scroll(self, direction):
        if not self.node.children:
            return

        if self.mode == 'viewer' and direction in ['up', 'down']:
            # up/down have no meaning in viewer mode so alias them to prev/next for convenience
            direction = 'prev' if direction == 'up' else 'next'

        if direction in ['prev', 'next']:
            self.scroll_node(direction == 'next')
        else:
            target_i = self.grid.get_target_i()
            n = len(self.node.children)
            if direction == 'top':
                target_i = 0
            elif direction == 'bottom':
                target_i = n - 1
            else:
                if self.mode == 'viewer':
                    assert direction in ['left', 'right']
                    target_i = (target_i + (1 if direction == 'right' else -1)) % n
                    self.viewer.load(self.node.children[target_i].abspath)
                else:
                    target_i = self.grid.neighbour(target_i, direction)
            self._set_target_i(target_i)

    def swap_cells(self, direction):
        cells = self.node.children
        target = self.get_target()
        if not target:
            return
        if direction in ['left', 'right']:
            i = (cells.index(target) + (1 if direction == 'right' else -1)) % len(cells)
            other = cells[i]
        elif self.mode == 'grid':
            other = cells[self.grid.neighbour(direction)]
        else:
            return # Cannot swap verticaly when in viewer mode
        try:
            target.swap_with(other)
            self.load_node(self.node, target)
        except TreeError as e:
            self.app.status_bar.set_text("Cannot swap (%s)" % e, duration_s=5)

    def select(self):
        if self.mode == 'viewer':
            self.set_mode('grid')
        else:
            node = self.get_target()
            if node:
                if node.children:
                    self.load_node(node, mode='grid')
                else:
                    self.viewer.load(node.abspath)
                    self.set_mode('viewer')

    def unselect(self):
        if self.mode == 'viewer':
            self.set_mode('grid')
        elif self.node.parent:
            self.load_node(self.node.parent, target=self.node, mode='grid')

    def handle_keydown(self, keystroke):
        action = self.keybinds.get_action(keystroke)
        if action in ['up', 'down', 'left', 'right', 'top', 'bottom', 'prev', 'next']:
            self.scroll(action)
        elif action in ['swap_up', 'swap_down', 'swap_left', 'swap_right']:
            self.swap_cells(action[len('swap_'):])
        elif action == 'select':
            self.select()
        elif action == 'unselect':
            self.unselect()
        elif action == 'toggle_hide':
            self.toggle_hide()
        else:
            return False
        return True
