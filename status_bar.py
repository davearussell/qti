import time
from PySide6.QtWidgets import QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import QObject, QTimer, Signal


class StatusBarWidget(QFrame):
    def __init__(self, text=''):
        super().__init__()
        self.setProperty("qtiOverlay", "true")

        self.setLayout(QHBoxLayout())
        self.label = QLabel()
        self.label.setProperty("qtiFont", "statusbar")
        self.set_text(text)
        self.layout().addWidget(self.label)

    def set_text(self, text):
        self.label.setText(text)


class StatusBar(QObject):
    text_update = Signal(str)

    def __init__(self):
        super().__init__()
        self.msg = ''
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh_msg)
        self.timed_msgs = [] # [ (msg, priority, expiry_time), ... ]
        self.perm_msg = None # (msg, priority)

    def set_text(self, msg, duration_s=None, priority=0):
        """
        Registers the specified message with the specified priority.
        If duration_s is specified, the message will expire after this duration.

        The message be displayed if it the highest priority message currently registered,
        If not, it may be displayed later if a higher priority message expires.

        In the case of a tie, timed messages take priority over permanent ones, and
        then more recently registered messages take priority over older ones.
        """
        if duration_s is not None:
            msg_key = ((msg, priority, time.time() + duration_s))
            self.timed_msgs.append(msg_key)
        else:
            if self.perm_msg is not None and self.perm_msg[1] > priority:
                return None
            msg_key = (msg, priority)
            self.perm_msg = msg_key
        self.refresh_msg()
        return msg_key

    def clear_text(self, msg_key):
        if msg_key in self.timed_msgs:
            self.timed_msgs.remove(msg_key)
            self.refresh_msg()
        elif msg_key == self.perm_msg:
            self.perm_msg = None
            self.refresh_msg()

    def refresh_msg(self):
        msg, prio = ('', None) if self.perm_msg is None else self.perm_msg
        now = time.time()
        first_expiry = None
        for item in list(self.timed_msgs):
            _msg, _prio, clear_at = item
            if clear_at < now:
                self.timed_msgs.remove(item)
                continue
            if first_expiry is None or clear_at < first_expiry:
                first_expiry = clear_at
            if prio is None or _prio >= prio:
                msg = _msg
                prio = _prio
        if msg != self.msg:
            self.msg = msg
            self.text_update.emit(msg)
        if first_expiry is not None:
            self.timer.start(1000 * (first_expiry - now))

    def make_widget(self):
        bar = StatusBarWidget(self.msg)
        self.text_update.connect(bar.set_text)
        return bar
