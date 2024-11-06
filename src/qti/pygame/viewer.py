from xui.widgets import Widget

class ViewerWidget(Widget):
    greedy_width = True
    greedy_height = True

    # Panning is expensive so only report mouse movement back to the app this often
    pan_batch_s = 0.2

    def __init__(self, app, mouse_cb):
        super().__init__()
        self.app = app
        self.mouse_cb = mouse_cb
        self.image = None
        self.mouse_down = False
        self.pending_pan = None
        self.mouse_pos = None

    def load(self, image):
        self.image = image
        self.redraw()

    def handle_mouse_down(self, button, pos):
        if button == 'left':
            self.mouse_down = True
            return self.mouse_cb('click', pos, None)
        elif button == 'wheelup':
            return self.mouse_cb('wheel', pos, 1)
        elif button == 'wheeldown':
            return self.mouse_cb('wheel', pos, -1)

    def handle_mouse_up(self, button, pos):
        if button == 'left':
            self.mouse_down = False
            if self.pending_pan:
                self.app.cancel_call(self.pending_pan)
                self.pan()

    def handle_mouse_move(self, pos):
        if self.mouse_down:
            self.mouse_pos = pos
            if not self.pending_pan:
                self.pending_pan = self.app.call_later(self.pan_batch_s, self.pan)

    def pan(self):
        self.pending_pan = None
        self.mouse_cb('drag', self.mouse_pos, None)

    def draw(self):
        super().draw()
        rect = self.image.image.get_rect()
        rect.center = (self.rect.width / 2, self.rect.height / 2)
        self.surface.blit(self.image.image, rect.topleft)
