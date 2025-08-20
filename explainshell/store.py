"""data objects to save processed man pages to mongodb"""

import pymongo, collections, re, logging

from explainshell import errors, util, helpconstants, config


logger = logging.getLogger(__name__)


class classifiermanpage(collections.namedtuple("classifiermanpage", "name paragraphs")):
    """a man page that had its paragraphs manually tagged as containing options
    or not"""

    @staticmethod
    def from_store(d):
        return classifiermanpage(
            d["name"], [paragraph.from_store(p) for p in d["paragraphs"]]
        )

    def to_store(self):
        return {
            "name": self.name,
            "paragraphs": [p.to_store() for p in self.paragraphs],
        }


class paragraph(object):
    """a paragraph inside a man page is text that ends with two new lines"""

    def __init__(self, idx, text, section, is_option):
        self.idx = idx
        self.text = text
        self.section = section
        self.is_option = is_option

    def cleantext(self):
        t = re.sub(r"<[^>]+>", "", self.text)
        t = re.sub("&lt;", "<", t)
        t = re.sub("&gt;", ">", t)
        return t

    @classmethod
    def from_store(cls, d):
        return cls(d.get("idx", 0), d["text"], d["section"], d["is_option"])

    def to_store(self):
        return {
            "idx": self.idx,
            "text": self.text,
            "section": self.section,
            "is_option": self.is_option,
        }

    def __repr__(self):
        t = self.cleantext()
        t = t[: min(20, t.find("\n"))].lstrip()
        return "<paragraph %d, %s: %r>" % (self.idx, self.section, t)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ if other else False


class option(paragraph):
    """a paragraph that contains extracted options

    short - a list of short options (-a, -b, ..)
    long - a list of long options (--a, --b)
    expectsarg - specifies if one of the short/long options expects an additional argument
    argument - specifies if to consider this as positional arguments
    nestedcommand - specifies if the arguments to this option can start a nested command
    """

    def __init__(self, p, short, long, expectsarg, argument=None, nestedcommand=False):
        paragraph.__init__(self, p.idx, p.text, p.section, p.is_option)
        self.short = short
        self.long = long
        self._opts = self.short + self.long
        self.argument = argument
        self.expectsarg = expectsarg
        self.nestedcommand = nestedcommand
        if nestedcommand:
            assert (
                expectsarg
            ), "an option that can nest commands must expect an argument"

    @property
    def opts(self):
        return self._opts

    @classmethod
    def from_store(cls, d):
        p = paragraph.from_store(d)

        return cls(
            p,
            d["short"],
            d["long"],
            d["expectsarg"],
            d["argument"],
            d.get("nestedcommand"),
        )

    def to_store(self):
        d = paragraph.to_store(self)
        assert d["is_option"]
        d["short"] = self.short
        d["long"] = self.long
        d["expectsarg"] = self.expectsarg
        d["argument"] = self.argument
        d["nestedcommand"] = self.nestedcommand
        return d

    def __str__(self):
        return f'({", ".join([str(x) for x in self.opts])})'

    def __repr__(self):
        return "<options for paragraph %d: %s>" % (self.idx, str(self))


class manpage(object):
    """processed man page

    source - the path to the original source man page
    name - the name of this man page as extracted by manpage.manpage
    synopsis - the synopsis of this man page as extracted by manpage.manpage
    paragraphs - a list of paragraphs (and options) that contain all of the text and options
        extracted from this man page
    aliases - a list of aliases found for this man page
    partialmatch - allow interperting options without a leading '-'
    multicommand - consider sub commands when explaining a command with this man page,
        e.g. git -> git commit
    updated - whether this man page was manually updated
    nestedcommand - specifies if positional arguments to this program can start a nested command,
        e.g. sudo, xargs
    """

    def __init__(
        self,
        source,
        name,
        synopsis,
        paragraphs,
        aliases,
        partialmatch=False,
        multicommand=False,
        updated=False,
        nestedcommand=False,
    ):
        self.source = source
        self.name = name
        self.synopsis = synopsis
        self.paragraphs = paragraphs
        self.aliases = aliases
        self.partialmatch = partialmatch
        self.multicommand = multicommand
        self.updated = updated
        self.nestedcommand = nestedcommand

    def removeoption(self, idx):
        for i, p in enumerate(self.paragraphs):
            if p.idx == idx:
                if not isinstance(p, option):
                    raise ValueError("paragraph %d isn't an option" % idx)
                self.paragraphs[i] = paragraph(p.idx, p.text, p.section, False)
                return
        raise ValueError("idx %d not found" % idx)

    @property
    def namesection(self):
        name, section = util.namesection(self.source[:-3])
        return f"{name}({section})"

    @property
    def section(self):
        name, section = util.namesection(self.source[:-3])
        return section

    @property
    def options(self):
        return [p for p in self.paragraphs if isinstance(p, option)]

    @property
    def arguments(self):
        # go over all paragraphs and look for those with the same 'argument'
        # field
        groups = collections.OrderedDict()
        for opt in self.options:
            if opt.argument:
                groups.setdefault(opt.argument, []).append(opt)

        # merge all the paragraphs under the same argument to a single string
        for k, l in groups.items():
            groups[k] = "\n\n".join([p.text for p in l])

        return groups

    @property
    def synopsisnoname(self):
        match = re.match(r"[\w|-]+ - (.*)$", self.synopsis)
        return match[1] if match else ""

    def find_option(self, flag):
        for option in self.options:
            for o in option.opts:
                if o == flag:
                    return option

    def to_store(self):
        return {
            "source": self.source,
            "name": self.name,
            "synopsis": self.synopsis,
            "paragraphs": [p.to_store() for p in self.paragraphs],
            "aliases": self.aliases,
            "partialmatch": self.partialmatch,
            "multicommand": self.multicommand,
            "updated": self.updated,
            "nestedcommand": self.nestedcommand,
        }

    @classmethod
    def from_store(cls, d):
        paragraphs = []
        for pd in d.get("paragraphs", []):
            pp = paragraph.from_store(pd)
            if pp.is_option == True and "short" in pd:
                pp = option.from_store(pd)
            paragraphs.append(pp)

        synopsis = d["synopsis"] or helpconstants.NOSYNOPSIS

        return cls(
            d["source"],
            d["name"],
            synopsis,
            paragraphs,
            [tuple(x) for x in d["aliases"]],
            bool(d.get("partialmatch", False)),
            bool(d.get("multicommand", False)),
            bool(d.get("updated", False)),
            d.get("nestedcommand", False),
        )

    @staticmethod
    def from_store_name_only(name, source):
        return manpage(source, name, None, [], [], False, False, False)

    def __repr__(self):
        return "<manpage %r(%s), %d options>" % (
            self.name,
            self.section,
            len(self.options),
        )


class store(object):
    """read/write processed man pages from mongodb

    we use three collections:
    1) classifier - contains manually tagged paragraphs from man pages
    2) manpage - contains a processed man page
    3) mapping - contains (name, manpageid, score) tuples
    """

    def __init__(self, db="explainshell", host=config.MONGO_URI):
        logger.info("creating store, db = %r, host = %r", db, host)
        self.connection = pymongo.MongoClient(host)
        self.db = self.connection[db]
        self.classifier = self.db["classifier"]
        self.manpage = self.db["manpage"]
        self.mapping = self.db["mapping"]

    def close(self):
        self.connection.close()
        self.classifier = None
        self.manpage = None
        self.mapping = None
        self.db = None

    def drop(self, confirm=False):
        if not confirm:
            return

        logger.info("dropping mapping, manpage, collections")
        if self.mapping is not None:
            self.mapping.drop()
        if self.manpage is not None:
            self.manpage.drop()

    def trainingset(self):
        if self.classifier is not None:
            for d in self.classifier.find():
                yield classifiermanpage.from_store(d)

    def __contains__(self, name):
        if self.mapping is None:
            return False
        c = self.mapping.count_documents({"src": name})
        return c > 0

    def __iter__(self):
        if self.manpage is None:
            return
        cursor = self.manpage.find() if self.manpage is not None else []
        for d in cursor:
            yield manpage.from_store(d)

    def findmanpage(self, name):
        """find a man page by its name, everything following the last dot (.) in name,
        is taken as the section of the man page

        we return the man page found with the highest score, and a list of
        suggestions that also matched the given name (only the first item
        is prepopulated with the option data)"""
        if name.endswith(".gz"):
            return self._extracted_from_findmanpage_9(name)
        section = None
        origname = name

        # don't try to look for a section if it's . (source)
        if name != ".":
            splitted = name.rsplit(".", 1)
            name = splitted[0]
            if len(splitted) > 1:
                section = splitted[1]

        logger.info("looking up manpage in mapping with src %r", name)
        if self.mapping is None or self.manpage is None:
            raise errors.ProgramDoesNotExist(name)
        cursor = self.mapping.find({"src": name})
        count = self.mapping.count_documents({"src": name})
        if not count:
            raise errors.ProgramDoesNotExist(name)

        dsts = {d["dst"]: d["score"] for d in cursor}
        cursor = self.manpage.find(
            {"_id": {"$in": list(dsts.keys())}}, {"name": 1, "source": 1}
        )
        cursor_count = self.manpage.count_documents({"_id": {"$in": list(dsts.keys())}})
        if cursor_count != len(dsts):
            logger.error(
                "one of %r mappings is missing in manpage collection "
                "(%d mappings, %d found)",
                dsts,
                len(dsts),
                cursor_count,
            )
        results = [(d.pop("_id"), manpage.from_store_name_only(**d)) for d in cursor]
        results.sort(key=lambda x: dsts.get(x[0], 0), reverse=True)
        logger.info("got %s", results)
        if section is not None:
            if len(results) > 1:
                results.sort(
                    key=lambda oid_m: oid_m[1].section == section, reverse=True
                )
                logger.info(r"sorting %r so %s is first", results, section)
            if results[0][1].section != section:
                raise errors.ProgramDoesNotExist(origname)
            results.extend(self._discovermanpagesuggestions(results[0][0], results))

        oid = results[0][0]
        results = [x[1] for x in results]
        if self.manpage is not None:
            doc = self.manpage.find_one({"_id": oid})
            if doc is not None:
                results[0] = manpage.from_store(doc)
        return results

    # TODO Rename this here and in `findmanpage`
    def _extracted_from_findmanpage_9(self, name):
        logger.info("name ends with .gz, looking up an exact match by source")
        d = self.manpage.find_one({"source": name}) if self.manpage is not None else None
        if not d:
            raise errors.ProgramDoesNotExist(name)
        m = manpage.from_store(d)
        logger.info("returning %s", m)
        return [m]

    def _discovermanpagesuggestions(self, oid, existing):
        """find suggestions for a given man page

        oid is the objectid of the man page in question,
        existing is a list of (oid, man page) of suggestions that were
        already discovered
        """
        skip = {oid for oid, m in existing}
        if self.mapping is None or self.manpage is None:
            return []
        cursor = self.mapping.find({"dst": oid})
        # find all srcs that point to oid
        srcs = [d["src"] for d in cursor]
        # find all dsts of srcs
        suggestionoids = self.mapping.find({"src": {"$in": srcs}}, {"dst": 1})
        # remove already discovered
        suggestionoids = [d["dst"] for d in suggestionoids if d["dst"] not in skip]
        if not suggestionoids:
            return []

        # get just the name and source of found suggestions
        if self.manpage is not None:
            suggestionoids_cursor = self.manpage.find(
                {"_id": {"$in": suggestionoids}}, {"name": 1, "source": 1}
            )
            return [
                (d.pop("_id"), manpage.from_store_name_only(**d)) for d in suggestionoids_cursor
            ]
        return []

    def addmapping(self, src, dst, score):
        if self.mapping is not None:
            self.mapping.insert_one({"src": src, "dst": dst, "score": score})

    def addmanpage(self, m):
        """add m into the store, if it exists first remove it and its mappings

        each man page may have aliases besides the name determined by its
        basename"""
        if self.manpage is not None:
            if d := self.manpage.find_one({"source": m.source}):
                self._extracted_from_addmanpage_8(m, d)
            result = self.manpage.insert_one(m.to_store())
            o = result.inserted_id

            for alias, score in m.aliases:
                self.addmapping(alias, o, score)
                logger.info(
                    "inserting mapping (alias) %s -> %s (%s) with score %d",
                    alias,
                    m.name,
                    o,
                    score,
                )
        return m

    # TODO Rename this here and in `addmanpage`
    def _extracted_from_addmanpage_8(self, m, d):
        if self.manpage is not None and self.mapping is not None:
            logger.info("removing old manpage %s (%s)", m.source, d["_id"])
            self.manpage.delete_one({"_id": d["_id"]})

            # remove old mappings if there are any
            c = self.mapping.count_documents({})
            self.mapping.delete_many({"dst": d["_id"]})
            c -= self.mapping.count_documents({})
            logger.info("removed %d mappings for manpage %s", c, m.source)

    def updatemanpage(self, m):
        """update m and add new aliases if necessary

        change updated attribute so we don't overwrite this in the future"""
        if self.manpage is not None:
            logger.info("updating manpage %s", m.source)
            m.updated = True
            self.manpage.update_one({"source": m.source}, {"$set": m.to_store()})
            doc = self.manpage.find_one({"source": m.source}, {"_id": 1})
            _id = doc["_id"] if doc is not None else None
            for alias, score in m.aliases:
                if alias not in self:
                    self.addmapping(alias, _id, score)
                    logger.info(
                        "inserting mapping (alias) %s -> %s (%s) with score %d",
                        alias,
                        m.name,
                        _id,
                        score,
                    )
                else:
                    logger.debug(
                        "mapping (alias) %s -> %s (%s) already exists", alias, m.name, _id
                    )
        return m

    def verify(self):
        # check that everything in manpage is reachable
        if self.mapping is None or self.manpage is None:
            return False, [], []
        mappings = list(self.mapping.find())
        reachable = {m["dst"] for m in mappings}
        manpages = {m["_id"] for m in self.manpage.find({}, {"_id": 1})}

        ok = True
        unreachable = manpages - reachable
        if unreachable:
            logger.error(
                "manpages %r are unreachable (nothing maps to them)", unreachable
            )
            unreachable_ids = unreachable
            unreachable = []
            if self.manpage is not None:
                for u in unreachable_ids:
                    doc = self.manpage.find_one({"_id": u})
                    if doc is not None and "name" in doc:
                        unreachable.append(doc["name"])
            ok = False

        notfound = reachable - manpages
        if notfound:
            logger.error("mappings to inexisting manpages: %r", notfound)
            ok = False

        return ok, unreachable, notfound

    def names(self):
        if self.manpage is not None:
            cursor = self.manpage.find({}, {"name": 1})
            for d in cursor:
                yield d["_id"], d["name"]

    def mappings(self):
        if self.mapping is not None:
            cursor = self.mapping.find({}, {"src": 1})
            for d in cursor:
                yield d["src"], d["_id"]

    def setmulticommand(self, manpageid):
        if self.manpage is not None:
            self.manpage.update_one({"_id": manpageid}, {"$set": {"multicommand": True}})
