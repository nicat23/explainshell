from explainshell import util


def convertparagraphs(manpage):
    for p in manpage.paragraphs:
        if isinstance(p.text, bytes):
            p.text = p.text.decode("utf-8", "ignore")
    return manpage


def suggestions(matches, command):
    """enrich command matches with links to other man pages with the
    same name"""
    for m in matches:
        if "name" in m and "suggestions" in m:
            before = command[: m["start"]]
            after = command[m["end"]:]
            newsuggestions = []
            for othermp in sorted(m["suggestions"], key=lambda mp: mp.section):
                mid = f"{othermp.name}.{othermp.section}"
                newsuggestions.append(
                    {"cmd": "".join([before, mid, after]),
                     "text": othermp.namesection}
                )
            m["suggestions"] = newsuggestions
