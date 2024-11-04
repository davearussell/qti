from PySide6.QtGui import QColor


def to_rgb(name):
    qcolor = QColor(name)
    if not qcolor.isValid():
        raise ValueError("'%s' is not a valid color" % (name,))
    return qcolor.red(), qcolor.green(), qcolor.blue()
