import os
import jinja2


def f_title(text):
    """Converts 'hello_world_i_am_a_title' -> 'Hello World I Am A Title' """
    return ' '.join(text.split('_')).title()


def f_lstrip(text):
    """Converts 'Prefix Interesting Title' -> 'Interesting Title'"""
    return ' '.join(text.split()[1:])


def f_rstrip(text):
    """Converts 'Interesting Title Suffix' -> 'Interesting Title'"""
    return ' '.join(text.split()[:-1])


def f_strip_words(text, *strip_words):
    pats = [word.lower() for word in strip_words]
    words = text.split()
    while words and any(re.match(pat, words[-1].lower()) for pat in pats):
        words = words[:-1]
    while words and any(re.match(pat, words[0].lower()) for pat in pats):
        words = words[1:]
    return ' '.join(words)


def f_strip_from(text, *strip_words):
    pats = [word.lower() for word in strip_words]
    words = text.split()
    for i, word in enumerate(words):
        if any(re.match(pat, word.lower()) for pat in pats):
            return ' '.join(words[:i])
    return ' '.join(words)


def f_strip_digits(text):
    return text.rstrip('0123456789')


def f_dirat(path, i):
    return path.split(os.path.sep)[int(i)]


def evaluate(node, template_string):
    env = jinja2.Environment()
    env.filters.update({
        'title': f_title,
        'lstrip': f_lstrip,
        'rstrip': f_rstrip,
        'strip_words': f_strip_words,
        'strip_from': f_strip_from,
        'strip_digits': f_strip_digits,
        'dirat': f_dirat,
    })

    spec = {
        'i': node.index,
        'name': node.name,
    }
    if node.type == 'image':
        spec.update({
            'dir': os.path.basename(os.path.dirname(node.abspath)),
            'file': os.path.splitext(os.path.basename(node.abspath))[0],
        })

    try:
        return env.from_string(template_string).render(spec)
    except jinja2.exceptions.TemplateError:
        return template_string
