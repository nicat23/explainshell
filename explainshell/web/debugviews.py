import logging

from flask import render_template, request, abort, redirect, url_for, json

from explainshell import manager, config, store
from explainshell.web import app, helpers

logger = logging.getLogger(__name__)


@app.route("/debug")
def debug():
    s = store.store("explainshell", config.MONGO_URI)
    d = {"manpages": []}
    for mp in s:
        synopsis = ""
        if mp.synopsis:
            synopsis = mp.synopsis[:20]
        l = []
        l.extend(str(o) for o in mp.options)
        dd = {"name": mp.name, "synopsis": synopsis, "options": ", ".join(l)}
        d["manpages"].append(dd)
    d["manpages"].sort(key=lambda d: d["name"].lower())
    return render_template("debug.html", d=d)


def _convertvalue(value):
    if isinstance(value, list):
        return [s.strip() for s in value]
    elif value.lower() == "true":
        return True
    elif value:
        return value.strip()
    return False


def _process_paragraphs(paragraphs_data):
    mparagraphs = []
    for d in paragraphs_data:
        short = [s.strip() for s in d["short"]]
        long = [s.strip() for s in d["long"]]
        expectsarg = _convertvalue(d["expectsarg"])
        nestedcommand = _convertvalue(d["nestedcommand"])
        
        # Only allow bool for nestedcommand, as required by store.option
        if isinstance(nestedcommand, list):
            nestedcommand = bool(nestedcommand)
        elif isinstance(nestedcommand, str):
            nestedcommand = bool(nestedcommand.strip())
        elif nestedcommand is not True and nestedcommand is not False:
            logger.error("nestedcommand %r must be a boolean, string, or list", nestedcommand)
            abort(503)
            
        p = store.paragraph(d["idx"], d["text"], d["section"], d["is_option"])
        if d["is_option"] and (short or long or d["argument"]):
            p = store.option(p, short, long, expectsarg, d["argument"] or None, nestedcommand)
        mparagraphs.append(p)
    return mparagraphs

@app.route("/debug/tag/<source>", methods=["GET", "POST"])
def tag(source):
    mngr = manager.manager(config.MONGO_URI, "explainshell", [], False, False)
    m = mngr.store.findmanpage(source)[0]
    assert m

    if "paragraphs" in request.form:
        paragraphs = json.loads(request.form["paragraphs"])
        mparagraphs = _process_paragraphs(paragraphs)
        m.nestedcommand = request.form.get("nestedcommand", "").lower() == "true"
        
        if m := mngr.edit(m, mparagraphs):
            return redirect(url_for("explain", cmd=m.name))
        else:
            abort(503)
    else:
        helpers.convertparagraphs(m)
        for p in m.paragraphs:
            if isinstance(p, store.option):
                if isinstance(p.expectsarg, list):
                    p.expectsarg = ", ".join(p.expectsarg)
                if isinstance(p.nestedcommand, list):
                    p.nestedcommand = bool(p.nestedcommand)
        return render_template("tagger.html", m=m)
