import re


def extract_first_line(paragraph):
    """
    >>> extract_first_line('a b  cd')
    'a b'
    >>> extract_first_line('a b cd')
    'a b cd'
    >>> extract_first_line('  a b cd')
    'a b cd'
    >>> extract_first_line('  a b   cd')
    'a b'
    """
    lines = paragraph.splitlines()
    first = lines[0].strip()
    if spaces := list(re.finditer(r"(\s+)", first)):
        longest = max(spaces, key=lambda m: m.span()[1] - m.span()[0])
        if longest and longest.start() > 1 and longest.end() - longest.start() > 1:
            first = first[: longest.start()]
    return first


def starts_with_hyphen(paragraph):
    stripped = paragraph.lstrip()
    return stripped and stripped[0] == "-"


def is_indented(paragraph):
    return paragraph != paragraph.lstrip()


def par_length(paragraph):
    return round(len(paragraph.strip()), -1) / 2


def first_line_contains(paragraph, what):
    l = paragraph.splitlines()[0]
    return what in l


def first_line_length(paragraph):
    first = extract_first_line(paragraph)
    return round(len(first), -1) / 2


def first_line_word_count(paragraph):
    first = extract_first_line(paragraph)
    splitted = [s for s in first.split() if len(s) > 1]

    return round(len(splitted), -1)


def is_good_section(paragraph):
    if not paragraph.section:
        return False
    s = paragraph.section.lower()
    return True if "options" in s else s in ("description", "function letters")


def word_count(text):
    return round(len(re.findall(r"\w+", text)), -1)


def has_bold(html):
    return "<b>" in html
