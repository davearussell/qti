import expr
from tree import SORT_TYPES
from keys import SCROLL_ACTIONS
from dialogs.deleter import delete_nodes

class MacroError(Exception):
    pass


def resolve_ref(app, ref):
    if '.' not in ref:
        return ref
    start, *args = ref.split('.')
    if not args:
        raise MacroError("Cannot resolve ref %r" % (ref,))

    if start == 'target' and 1 <= len(args) <= 2:
        value = app.browser.target.get_key(args.pop(0))
        if args:
            value = value[int(args.pop())]
        return value

    if start == 'browser':
        if args == ['mode']:
            return app.browser.mode
        if args == ['target']:
            return app.browser.target
        if args == ['marked']:
            return app.browser.marked_nodes()

    raise MacroError("Cannot resolve ref %r" % (ref,))


def tokenize(line):
    token_start = None
    for i, char in enumerate(line):
        is_sep = char.isspace() or char in '#:'
        if is_sep:
            if token_start is not None:
                yield line[token_start:i]
            yield line[i]
            token_start = None
        elif token_start is None:
            token_start = i
    if token_start is not None:
        yield line[token_start:]


class Command:
    command = None
    min_args = None
    max_args = None

    def __init__(self, app, args):
        self.app = app
        self._args = args
        if self.min_args is not None and len(args) < self.min_args:
            self.bad_args("require >= %d args" % (self.min_args,))
        if self.max_args is not None and len(args) > self.max_args:
            self.bad_args("require <= %d args" % (self.max_args,))
        self.process_args(args)

    def process_args(self, args):
        pass

    def bad_args(self, msg):
        raise MacroError("%s %s: %s" % (type(self).__name__.lower(), ' '.join(self._args), msg))

    @classmethod
    def command_map(cls):
        commands = {}
        for subcls in cls.__subclasses__():
            if subcls.command:
                commands[subcls.command] = subcls
            commands |= subcls.command_map()
        return commands

    @classmethod
    def syntax_highlight(cls, text):
        pos = 0
        comment = False
        done_command = False
        for token in tokenize(text):
            if token == '#':
                comment = True
            word_type = None
            if comment:
                word_type = 'comment'
            elif not done_command and not token.isspace():
                word_type = 'command' if token in cls.command_map() else 'error'
                done_command = True
            elif '.' in token:
                word_type = 'variable'
            yield pos, len(token), word_type
            pos += len(token)


class Group(Command):
    command = 'group'

    def process_args(self, args):
        self.clauses = []
        for arg in args:
            if ':' in arg:
                key, include = arg.split(':')
            else:
                key, include = arg, None

            clause = resolve_ref(self.app, key)

            if include:
                include = resolve_ref(self.app, include)
                if isinstance(include, list):
                    include = ','.join(map(str, include))
                clause += ':' + include
            self.clauses.append(clause)

    def run(self):
        self.app.filter_config.group_by = self.clauses


class Order(Command):
    command = 'order'

    def process_args(self, args):
        self.clauses = [resolve_ref(self.app, arg) for arg in args]
        for clause in self.clauses:
            if clause not in SORT_TYPES:
                self.bad_args("unknown sort type")

    def run(self):
        self.app.filter_config.order_by = self.clauses


class Expr(Command):
    command = 'expr'

    @staticmethod
    def _walk_tags(ex):
        if isinstance(ex, expr.Tag):
            yield ex
        elif isinstance(ex, expr.Prefix):
            yield from walk_expr(ex.value)
        elif isinstance(ex, expr.Infix):
            yield from walk_expr(ex.lhs)
            yield from walk_expr(ex.rhs)
        elif not isinstance(ex, expr.Empty):
            assert 0, ex

    def process_args(self, args):
        try:
            self.expr = expr.parse_expr(' '.join(args))
        except expr.BadExpr:
            self.bad_args("cannot parse expr")
        for tag in self._walk_tags(self.expr):
            tag.value = resolve_ref(app, tag.value)

    def run(self):
        self.app.filter_config.include_tags = []
        self.app.filter_config.exclude_tags = []
        self.app.filter_config.custom_expr = self.expr


class Snapshot(Command):
    command = 'snapshot'
    max_args = 0

    def run(self):
        self.app.save_snapshot()

class Reload(Command):
    command = 'reload'
    max_args = 0

    def run(self):
        self.app.reload_tree()


class Load(Command):
    command = 'load'
    min_args = 1

    def process_args(self, args):
        args = [resolve_ref(self.app, arg) for arg in args]
        self.mode, *self.path = args
        if self.mode not in ['grid', 'viewer']:
            self.bad_args('expected load <grid|viewer> ...')

    def run(self):
        node = self.app.library.make_tree(self.app.filter_config)
        for name in self.path:
            for child in node.children:
                if child.name == name:
                    node = child
                    break
            else:
                raise MacroError("Cannot load path %r" % (self.path,))
        if self.mode == 'viewer':
            target = node
            while target.children:
                target = target.children[0]
            node = target.parent
        else:
            target = None
        self.app.browser.load_node(node, target, self.mode)


class Edit(Command):
    command = 'edit'
    min_args = 2

    def process_args(self, args):
        args = [resolve_ref(self.app, arg) for arg in args]
        self.key, self.op, *self.value = args
        if self.key not in self.app.metadata.editable_keys():
            self.bad_args("is read-only")
        self.is_multi = self.key in self.app.metadata.multi_value_keys()
        if self.op == 'set':
            if not self.is_multi:
                if len(self.value) != 1:
                    self.bad_args("one value required")
                self.value = self.value[0]
        elif self.op in ['add', 'remove', 'toggle']:
            if not self.is_multi:
                self.bad_args("op requres a multi-value key")
        else:
            self.bad_args("unknown op")

    def run(self):
        target = self.app.browser.target
        if self.op == 'set':
            target.update(self.key, self.value)
        else:
            target.update_set(self.key, **{self.op: set(self.value)})


class Delete(Command):
    command = 'delete'
    min_args = 1
    max_args = 2

    def process_args(self, args):
        nodes = resolve_ref(self.app, args[0])
        if not isinstance(nodes, list):
            nodes = [nodes]
        self.nodes = nodes
        self.mode = args[1] if len(args) == 2 else 'library'

    def run(self):
        delete_nodes(self.app, self.nodes, self.mode)


class Scroll(Command):
    command = 'scroll'
    min_args = 1
    max_args = 1

    def process_args(self, args):
        self.direction = args[0]
        if self.direction not in SCROLL_ACTIONS:
            self.bad_args('invalid scroll direction')

    def run(self):
        self.app.browser.scroll(self.direction)


def parse_macro(app, macro):
    command_map = Command.command_map()
    commands = []
    for line in macro.strip().split('\n'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        command, *args = line.split()
        if '.' in command:
            command = resolve_ref(app, command)
        if command not in command_map:
            raise MacroError("Unknown command %r" % (command,))
        commands.append(command_map[command](app, args))
    return commands


def run_macro(app, macro):
    for command in parse_macro(app, macro):
        command.run()
