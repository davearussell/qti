from .qt.pathbar import PathbarWidget


class PathbarEntry:
    def __init__(self, name, index, total, fade, ctx=None):
        self.name = name
        self.index = index
        self.total = total
        self.fade = fade
        self.ctx = ctx


class Pathbar:
    def __init__(self, click_cb):
        self.click_cb = click_cb
        self.ui = PathbarWidget(self.entry_clicked)
        self.fade_target = False

    def entry_clicked(self, entry):
        self.click_cb(entry.ctx)

    def set_target(self, target):
        entries = []
        node = target
        while node and node.parent:
            entry = PathbarEntry(name=node.name,
                                 index=node.parent.children.index(node),
                                 total=len(node.parent.children),
                                 fade=self.fade_target and node is target,
                                 ctx=node)
            entries.insert(0, entry)
            node = node.parent
        self.ui.set_entries(entries)
