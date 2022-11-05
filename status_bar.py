import time
from PySide6.QtWidgets import QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import QObject, QTimer, Signal


class StatusBarWidget(QFrame):
    def __init__(self, text=''):
        super().__init__()
        self.setProperty("qtiColors", "semitransparent")

        self.setLayout(QHBoxLayout())
        self.label = QLabel()
        self.label.setProperty("qtiColors", "transparent")
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
        self.perm_msg = ''
        self.perm_prio = None
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh_msg)
        self.timed_msgs = [] # [ (msg, priority), ... ]

    def set_text(self, msg, duration_s=None, priority=0):
        """
        Registers the specified message with the specified priority.
        If duration_s is specified, the message will expire after this duration.

        The message be displayed if it the highest priority message currently registered,
        If not, it may be displayed later if a higher priority message expires.

        In the case of a tie, timed messages take priority over permanent ones, and
        then more recently registered messages take priority over older ones.
        """
        if self.perm_prio is not None and self.perm_prio > priority:
            return
        if duration_s is None:
            self.perm_prio = priority
            self.perm_msg = msg
        else:
            self.timed_msgs.append((msg, priority, time.time() + duration_s))
        self.refresh_msg()

    def refresh_msg(self):
        msg = self.perm_msg
        prio = self.perm_prio
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
