import ast
import io
import keyword
import tokenize

INTERESTING_TYPES = {'NAME', 'STRING', 'COMMENT', 'KEYWORD'}

class Token:
    def __init__(self, rawtoken):
        self.type = tokenize.tok_name[rawtoken.type]
        if self.type == 'NAME' and keyword.iskeyword(rawtoken.string):
            self.type = 'KEYWORD'
        if self.type not in INTERESTING_TYPES:
            self.type = 'IGNORE'
        self.start_line, self.start_pos = rawtoken.start
        self.end_line, self.end_pos = rawtoken.end
        self.start_line -= 1
        self.end_line -= 1

    def __repr__(self):
        return "%s(%d/%d - %d/%d" % (self.type, self.start_line, self.start_pos, self.end_line, self.end_pos)


class Filler(Token):
    def __init__(self, start_line, start_pos, end_line, end_pos):
        self.type = 'IGNORE'
        self.start_line = start_line
        self.start_pos = start_pos
        self.end_line = end_line
        self.end_pos = end_pos


def _merge_tokens(tokens):
    merged_tokens = []
    for token in tokens:
        if merged_tokens and merged_tokens[-1].type == token.type:
            merged_tokens[-1].end_line = token.end_line
            merged_tokens[-1].end_pos = token.end_pos
        else:
            merged_tokens.append(token)
    return merged_tokens


def lex(text):
    lines = text.split('\n')
    end_line = len(lines) - 1
    end_pos = len(lines[end_line])

    tokens = []
    cur_line = cur_pos = 0

    try:
        for rawtoken in tokenize.generate_tokens(io.StringIO(text).readline):
            token = Token(rawtoken)
            if (token.start_line, token.start_pos) != (cur_line, cur_pos):
                tokens.append(Filler(cur_line, cur_pos, token.start_line, token.start_pos))
            tokens.append(token)
            cur_line = token.end_line
            cur_pos = token.end_pos
    except Exception as e:
        print("Invalid macro:", e)

    if (cur_line < end_line) or (cur_line == end_line and cur_pos < end_pos):
        tokens.append(Filler(cur_line, cur_pos, end_line, end_pos))
    return _merge_tokens(tokens)


def _highlight_line(line_i, line, tokens):
    words = []
    for token in tokens:
        if token.start_line > line_i:
            break
        if token.end_line < line_i:
            continue

        start_pos = 0 if token.start_line < line_i else token.start_pos
        end_pos = len(line) if token.end_line > line_i else token.end_pos
        word = line[start_pos:end_pos]
        if word:
            words.append((word, token.type))
    return words


def syntax_highlight(text):
    tokens = lex(text)
    lines = text.split('\n')
    return [_highlight_line(i, line, tokens) for i, line in enumerate(lines)]


def run_macro(app, macro):
    tree = ast.parse(macro)
    code = compile(tree, '<macro>', 'exec')
    exec(code, {'app': app})
