import itertools
import logging
import urllib.parse

import bashlex.errors
import markupsafe
from flask import render_template, request, redirect

from explainshell import config, errors, matcher, store, util
from explainshell.web import app, helpers

logger = logging.getLogger(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/explain")
def explain():
    if "cmd" not in request.args or not request.args["cmd"].strip():
        return redirect("/")
    command = request.args["cmd"].strip()
    command = command[:1000]  # trim commands longer than 1000 characters
    if "\n" in command:
        return render_template(
            "errors/error.html",
            title="parsing error!",
            message="no newlines please",
        )

    s = store.store("explainshell", config.MONGO_URI)
    try:
        matches, helptext = explaincommand(command, s)
        return render_template(
            "explain.html", matches=matches, helptext=helptext, getargs=command
        )

    except errors.ProgramDoesNotExist:
        return render_template(
            "errors/missingmanpage.html", title="missing man page"
        )
    except bashlex.errors.ParsingError as e:
        logger.warn("%r parsing error: %s", command, e.message)
        return render_template("errors/parsingerror.html",
                               title="parsing error!", e=e)
    except NotImplementedError as e:
        logger.warn("not implemented error trying to explain %r", command)
        msg = (
            "the parser doesn't support %r constructs in the command you"
            "tried. You may"
            "<a href='https://github.com/idank/explainshell/issues'> "
            "report a bug</a> to have this added, "
            "if one doesn't already exist."
        ) % e.args[0]

        return render_template("errors/error.html",
                               title="error!", message=msg)
    except Exception:
        logger.error("uncaught exception trying to explain %r",
                     command, exc_info=True)
        msg = "something went wrong... this was logged and will be checked"
        return render_template("errors/error.html",
                               title="error!", message=msg)


@app.route("/explain/<program>", defaults={"section": None})
@app.route("/explain/<section>/<program>")
def explainold(section, program):
    logger.info("/explain section=%r program=%r", section, program)

    s = store.store("explainshell", config.MONGO_URI)
    if section is not None:
        program = f"{program}.{section}"

    # keep links to old urls alive
    if "args" in request.args:
        args = request.args["args"]
        command = f"{program} {args}"
        quoted_command = urllib.parse.quote_plus(command)
        return redirect(f"/explain?cmd={quoted_command}", 301)
    else:
        try:
            mp, suggestions = explainprogram(program, s)
            return render_template("options.html",
                                   mp=mp, suggestions=suggestions)
        except errors.ProgramDoesNotExist as e:
            return render_template(
                "errors/missingmanpage.html", title="missing man page", e=e
            )


def explainprogram(program, store):
    mps = store.findmanpage(program)
    mp = mps.pop(0)
    program = mp.namesection

    synopsis = mp.synopsis

    mp = {
        "source": mp.source[:-3],
        "section": mp.section,
        "program": program,
        "synopsis": synopsis,
        "options": [o.text for o in mp.options],
    }

    suggestions = []
    for othermp in mps:
        d = {
            "text": othermp.namesection,
            "link": f"{othermp.section}/{othermp.name}",
        }
        suggestions.append(d)
    logger.info("suggestions: %s", suggestions)
    return mp, suggestions


def _makematch(start, end, match, commandclass, helpclass):
    return {
        "match": match,
        "start": start,
        "end": end,
        "spaces": "",
        "commandclass": commandclass,
        "helpclass": helpclass,
    }


def _process_group_results(group,
                           texttoid,
                           idstartpos,
                           expansions,
                           is_shell=False):
    """Process results from a match group and return formatted matches."""
    matches = []
    for m in group.results:
        commandclass = group.name
        helpclass = "help-%d" % len(texttoid)
        if text := m.text:
            helpclass = texttoid.setdefault(text, helpclass)
        else:
            commandclass += " unknown"
            helpclass = ""
        if helpclass:
            idstartpos.setdefault(helpclass, m.start)

        d = _makematch(m.start, m.end, m.match, commandclass, helpclass)
        formatmatch(d, m, expansions)
        matches.append(d)
    return matches


def _add_command_metadata(matches, commandgroup):
    """Add command metadata to the first match in a command group."""
    if not matches:
        return

    d = matches[0]
    d["commandclass"] += " simplecommandstart"

    if getattr(commandgroup, "manpage", None) is not None:
        d["name"] = commandgroup.manpage.name
        d["section"] = commandgroup.manpage.section
        if "." not in d["match"]:
            d["match"] = f'{d["match"]}({d["section"]})'
        d["suggestions"] = commandgroup.suggestions
        d["source"] = commandgroup.manpage.source[:-5]


def explaincommand(command, store):
    matcher_ = matcher.matcher(command, store)
    groups = matcher_.match()
    expansions = matcher_.expansions

    texttoid = {}
    idstartpos = {}

    # Process shell group
    shell_matches = _process_group_results(
        groups[0], texttoid, idstartpos, expansions, True
    )
    all_matches = [shell_matches]

    # Process command groups
    for commandgroup in groups[1:]:
        cmd_matches = _process_group_results(
            commandgroup, texttoid, idstartpos, expansions
        )
        _add_command_metadata(cmd_matches, commandgroup)
        all_matches.append(cmd_matches)

    matches = list(itertools.chain.from_iterable(all_matches))
    helpers.suggestions(matches, command)
    matches.sort(key=lambda d: d["start"])

    # Add spacing between matches
    it = util.peekable(iter(matches))
    while it.hasnext():
        m = next(it)
        if m is None:
            continue
        spaces = 0
        if it.hasnext():
            peeked = it.peek()
            if peeked is not None:
                spaces = peeked["start"] - m["end"]
        m["spaces"] = " " * spaces

    helptext = sorted(texttoid.items(), key=lambda k_v: idstartpos[k_v[1]])
    return matches, helptext


def formatmatch(d, m, expansions):
    """populate the match field in d by escaping m.match and generating
    links to any command/process substitutions"""

    hassubsinmatch = any(
        m.start <= start and end <= m.end for start, end, kind in expansions
    )
    # if not, just escape the current match
    if not hassubsinmatch:
        d["match"] = markupsafe.escape(m.match)
        return

    # used in es.js
    d["commandclass"] += " hasexpansion"

    # go over the expansions, wrapping them with a link; leave everything else
    # untouched
    expandedmatch = ""
    i = 0
    for start, end, kind in expansions:
        if start >= m.end:
            break
        relativestart = start - m.start
        relativeend = end - m.start

        if i < relativestart:
            for j in range(i, relativestart):
                if m.match[j].isspace():
                    expandedmatch += markupsafe.Markup("&nbsp;")
                else:
                    expandedmatch += markupsafe.escape(m.match[j])
            i = relativestart + 1
        if m.start <= start and end <= m.end:
            s = m.match[relativestart:relativeend]

            if kind == "substitution":
                content = markupsafe.Markup(_substitutionmarkup(s))
            else:
                content = s

            expandedmatch += markupsafe.Markup(
                '<span class="expansion-{0}">{1}</span>'
            ).format(kind, content)
            i = relativeend

    if i < len(m.match):
        expandedmatch += markupsafe.escape(m.match[i:])

    assert expandedmatch
    d["match"] = expandedmatch


def _substitutionmarkup(cmd):
    """Generate markup for command substitution links.
    
    Args:
        cmd: Command string to create link for
        
    Returns:
        HTML anchor tag with encoded command URL
    """
    encoded = urllib.parse.quote_plus(cmd)
    return (
        '<a href="/explain?cmd={query}" '
        'title="Zoom in to nested command">{cmd}</a>'
    ).format(cmd=cmd, query=encoded)


def _checkoverlaps(s, matches):
    explained = [None] * len(s)
    for d in matches:
        for i in range(d["start"], d["end"]):
            if explained[i]:
                raise RuntimeError(
                    "explained overlap for group %s at %d with %s"
                    % (d, i, explained[i])
                )
            explained[i] = d
