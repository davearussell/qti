import operator
import lark

class BadExpr(Exception):
    pass

grammar = """
?start: expr | -> do_empty
?expr: prefix_expr | infix_expr

PREFIX_OP: "!"
?prefix_expr: value
            | PREFIX_OP value -> do_prefix

INFIX_OP: "|" | "&"
infix_expr: expr INFIX_OP prefix_expr -> do_infix

?value: CNAME -> do_tag
      | "(" expr ")"

%import common.CNAME
%import common.WS
%ignore WS
"""


class Tag:
    def __init__(self, arg):
        self.value = arg[0]

    def __str__(self):
        return str(self.value)

    def matches(self, tags):
        return self.value in tags


class Infix:
    def __init__(self, arg):
        self.lhs, self.symbol, self.rhs = arg
        self.op = {
            '&': operator.and_,
            '|': operator.or_,
        }[self.symbol]

    def __str__(self):
        return "(%s %s %s)" % (self.lhs, self.symbol, self.rhs)

    def matches(self, tags):
        return self.op(self.lhs.matches(tags), self.rhs.matches(tags))


class Prefix:
    def __init__(self, arg):
        self.symbol, self.value = arg
        self.op = {
            '!': operator.not_,
        }[self.symbol]

    def __str__(self):
        return "%s%s" % (self.symbol, self.value)

    def matches(self, tags):
        return self.op(self.value.matches(tags))


class Empty:
    def __init__(self, arg):
        assert not arg

    def __str__(self):
        return ''

    def matches(self, tags):
        return True


class Tree(lark.Transformer):
    do_tag = Tag
    do_infix = Infix
    do_prefix = Prefix
    do_empty = Empty


parser = lark.Lark(grammar, parser='lalr', transformer=Tree())

def parse_expr(text):
    try:
        return parser.parse(text)
    except lark.LarkError as e:
        raise BadExpr() from e
