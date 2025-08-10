'''data objects to save processed man pages to mongodb'''
import pymongo
import collections
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Iterator, NamedTuple

from explainshell import errors, util, helpconstants, config

logger = logging.getLogger(__name__)

class classifiermanpage(NamedTuple):
    '''a man page that had its paragraphs manually tagged as containing options
    or not'''
    name: str
    paragraphs: List['paragraph']
    
    @staticmethod
    def from_store(d: Dict[str, Any]) -> 'classifiermanpage':
        m = classifiermanpage(d['name'], [paragraph.from_store(p) for p in d['paragraphs']])
        return m

    def to_store(self) -> Dict[str, Any]:
        return {'name': self.name,
                'paragraphs': [p.to_store() for p in self.paragraphs]}

class paragraph:
    '''a paragraph inside a man page is text that ends with two new lines'''
    def __init__(self, idx: int, text: str, section: str, is_option: bool):
        self.idx = idx
        self.text = text
        self.section = section
        self.is_option = is_option

    def cleantext(self) -> str:
        t = re.sub(r'<[^>]+>', '', self.text)
        t = re.sub('&lt;', '<', t)
        t = re.sub('&gt;', '>', t)
        return t

    @staticmethod
    def from_store(d: Dict[str, Any]) -> 'paragraph':
        # Python 3: no need to encode to utf8, strings are unicode by default
        p = paragraph(d.get('idx', 0), d['text'], d['section'], d['is_option'])
        return p

    def to_store(self) -> Dict[str, Any]:
        return {'idx': self.idx, 'text': self.text, 'section': self.section,
                'is_option': self.is_option}

    def __repr__(self) -> str:
        t = self.cleantext()
        t = t[:min(20, t.find('\n'))].lstrip()
        return '<paragraph %d, %s: %r>' % (self.idx, self.section, t)

    def __eq__(self, other) -> bool:
        if not other:
            return False
        return self.__dict__ == other.__dict__

class option(paragraph):
    '''a paragraph that contains extracted options

    short - a list of short options (-a, -b, ..)
    long - a list of long options (--a, --b)
    expectsarg - specifies if one of the short/long options expects an additional argument
    argument - specifies if to consider this as positional arguments
    nestedcommand - specifies if the arguments to this option can start a nested command
    '''
    def __init__(self, p: paragraph, short: List[str], long: List[str], 
                 expectsarg: bool, argument: Optional[str] = None, 
                 nestedcommand: bool = False):
        paragraph.__init__(self, p.idx, p.text, p.section, p.is_option)
        self.short = short
        self.long = long
        self._opts = self.short + self.long
        self.argument = argument
        self.expectsarg = expectsarg
        self.nestedcommand = nestedcommand
        if nestedcommand:
            assert expectsarg, 'an option that can nest commands must expect an argument'

    @property
    def opts(self) -> List[str]:
        return self._opts

    @classmethod
    def from_store(cls, d: Dict[str, Any]) -> 'option':
        p = paragraph.from_store(d)

        return cls(p, d['short'], d['long'], d['expectsarg'], d['argument'],
                   d.get('nestedcommand'))

    def to_store(self) -> Dict[str, Any]:
        d = paragraph.to_store(self)
        assert d['is_option']
        d['short'] = self.short
        d['long'] = self.long
        d['expectsarg'] = self.expectsarg
        d['argument'] = self.argument
        d['nestedcommand'] = self.nestedcommand
        return d

    def __str__(self) -> str:
        return '(%s)' % ', '.join([str(x) for x in self.opts])

    def __repr__(self) -> str:
        return '<options for paragraph %d: %s>' % (self.idx, str(self))

class manpage:
    '''processed man page

    source - the path to the original source man page
    name - the name of this man page as extracted by manpage.manpage
    synopsis - the synopsis of this man page as extracted by manpage.manpage
    paragraphs - a list of paragraphs (and options) that contain all of the text and options
        extracted from this man page
    aliases - a list of aliases found for this man page
    partialmatch - allow interpreting options without a leading '-'
    multicommand - consider sub commands when explaining a command with this man page,
        e.g. git -> git commit
    updated - whether this man page was manually updated
    nestedcommand - specifies if positional arguments to this program can start a nested command,
        e.g. sudo, xargs
    '''
    def __init__(self, source: str, name: str, synopsis: Optional[str], 
                 paragraphs: List[paragraph], aliases: List[Tuple[str, int]],
                 partialmatch: bool = False, multicommand: bool = False, 
                 updated: bool = False, nestedcommand: bool = False):
        self.source = source
        self.name = name
        self.synopsis = synopsis
        self.paragraphs = paragraphs
        self.aliases = aliases
        self.partialmatch = partialmatch
        self.multicommand = multicommand
        self.updated = updated
        self.nestedcommand = nestedcommand

    def removeoption(self, idx: int) -> None:
        for i, p in enumerate(self.paragraphs):
            if p.idx == idx:
                if not isinstance(p, option):
                    raise ValueError("paragraph %d isn't an option" % idx)
                self.paragraphs[i] = paragraph(p.idx, p.text, p.section, False)
                return
        raise ValueError('idx %d not found' % idx)

    @property
    def namesection(self) -> str:
        name, section = util.namesection(self.source[:-3])
        return '%s(%s)' % (name, section)

    @property
    def section(self) -> str:
        name, section = util.namesection(self.source[:-3])
        return section

    @property
    def options(self) -> List[option]:
        return [p for p in self.paragraphs if isinstance(p, option)]

    @property
    def arguments(self) -> Dict[str, str]:
        # go over all paragraphs and look for those with the same 'argument'
        # field
        groups = collections.OrderedDict()
        for opt in self.options:
            if opt.argument:
                groups.setdefault(opt.argument, []).append(opt)

        # merge all the paragraphs under the same argument to a single string
        # Python 3: dict.items() instead of iteritems()
        for k, l in groups.items():
            groups[k] = '\n\n'.join([p.text for p in l])

        return groups

    @property
    def synopsisnoname(self) -> str:
        match = re.match(r'[\w|-]+ - (.*)$', self.synopsis)
        return match.group(1) if match else ''

    def find_option(self, flag: str) -> Optional[option]:
        for option_obj in self.options:
            for o in option_obj.opts:
                if o == flag:
                    return option_obj
        return None

    def to_store(self) -> Dict[str, Any]:
        return {'source': self.source, 'name': self.name, 'synopsis': self.synopsis,
                'paragraphs': [p.to_store() for p in self.paragraphs],
                'aliases': self.aliases, 'partialmatch': self.partialmatch,
                'multicommand': self.multicommand, 'updated': self.updated,
                'nestedcommand': self.nestedcommand}

    @staticmethod
    def from_store(d: Dict[str, Any]) -> 'manpage':
        paragraphs = []
        for pd in d.get('paragraphs', []):
            pp = paragraph.from_store(pd)
            if pp.is_option == True and 'short' in pd:
                pp = option.from_store(pd)
            paragraphs.append(pp)

        synopsis = d['synopsis']
        if synopsis:
            # Python 3: no need to encode to utf8, strings are unicode by default
            pass
        else:
            synopsis = helpconstants.NOSYNOPSIS

        return manpage(d['source'], d['name'], synopsis, paragraphs,
                       [tuple(x) for x in d['aliases']], d['partialmatch'],
                       d['multicommand'], d['updated'], d.get('nestedcommand'))

    @staticmethod
    def from_store_name_only(name: str, source: str) -> 'manpage':
        return manpage(source, name, None, [], [], None, None, None)

    def __repr__(self) -> str:
        return '<manpage %r(%s), %d options>' % (self.name, self.section, len(self.options))

class store:
    '''read/write processed man pages from mongodb

    we use three collections:
    1) classifier - contains manually tagged paragraphs from man pages
    2) manpage - contains a processed man page
    3) mapping - contains (name, manpageid, score) tuples
    '''
    def __init__(self, db: str = 'explainshell', host: str = config.MONGO_URI):
        logger.info('creating store, db = %r, host = %r', db, host)
        self.connection = pymongo.MongoClient(host)
        self.db = self.connection[db]
        self.classifier = self.db['classifier']
        self.manpage = self.db['manpage']
        self.mapping = self.db['mapping']

    def close(self) -> None:
        self.connection.close()  # Python 3: close() instead of disconnect()
        self.classifier = self.manpage = self.mapping = self.db = None

    def drop(self, confirm: bool = False) -> None:
        if not confirm:
            return

        logger.info('dropping mapping, manpage, collections')
        self.mapping.drop()
        self.manpage.drop()

    def trainingset(self) -> Iterator[classifiermanpage]:
        for d in self.classifier.find():
            yield classifiermanpage.from_store(d)

    def __contains__(self, name: str) -> bool:
        # Python 3: count_documents() instead of count()
        c = self.mapping.count_documents({'src': name})
        return c > 0

    def __iter__(self) -> Iterator[manpage]:
        for d in self.manpage.find():
            yield manpage.from_store(d)

    def findmanpage(self, name: str) -> List[manpage]:
        '''find a man page by its name, everything following the last dot (.) in name,
        is taken as the section of the man page

        we return the man page found with the highest score, and a list of
        suggestions that also matched the given name (only the first item
        is prepopulated with the option data)'''
        if name.endswith('.gz'):
            logger.info('name ends with .gz, looking up an exact match by source')
            d = self.manpage.find_one({'source': name})
            if not d:
                raise errors.ProgramDoesNotExist(name)
            m = manpage.from_store(d)
            logger.info('returning %s', m)
            return [m]

        section = None
        origname = name

        # don't try to look for a section if it's . (source)
        if name != '.':
            splitted = name.rsplit('.', 1)
            name = splitted[0]
            if len(splitted) > 1:
                section = splitted[1]

        logger.info('looking up manpage in mapping with src %r', name)
        cursor = self.mapping.find({'src': name})
        count = self.mapping.count_documents({'src': name})  # Python 3: count_documents()
        if not count:
            raise errors.ProgramDoesNotExist(name)

        dsts = dict(((d['dst'], d['score']) for d in cursor))
        cursor = self.manpage.find({'_id': {'$in': list(dsts.keys())}}, {'name': 1, 'source': 1})
        cursor_count = self.manpage.count_documents({'_id': {'$in': list(dsts.keys())}})
        if cursor_count != len(dsts):
            logger.error('one of %r mappings is missing in manpage collection '
                         '(%d mappings, %d found)', dsts, len(dsts), cursor_count)
        results = [(d.pop('_id'), manpage.from_store_name_only(**d)) for d in cursor]
        results.sort(key=lambda x: dsts.get(x[0], 0), reverse=True)
        logger.info('got %s', results)
        if section is not None:
            if len(results) > 1:
                # Python 3: lambda parameters can't be unpacked
                results.sort(key=lambda item: item[1].section == section, reverse=True)
                logger.info(r'sorting %r so %s is first', results, section)
            if not results[0][1].section == section:
                raise errors.ProgramDoesNotExist(origname)
            results.extend(self._discovermanpagesuggestions(results[0][0], results))

        oid = results[0][0]
        results = [x[1] for x in results]
        results[0] = manpage.from_store(self.manpage.find_one({'_id': oid}))
        return results

    def _discovermanpagesuggestions(self, oid: Any, existing: List[Tuple[Any, manpage]]) -> List[Tuple[Any, manpage]]:
        '''find suggestions for a given man page

        oid is the objectid of the man page in question,
        existing is a list of (oid, man page) of suggestions that were
        already discovered
        '''
        skip = set([oid for oid, m in existing])
        cursor = self.mapping.find({'dst': oid})
        # find all srcs that point to oid
        srcs = [d['src'] for d in cursor]
        # find all dsts of srcs
        suggestionoids = self.mapping.find({'src': {'$in': srcs}}, {'dst': 1})
        # remove already discovered
        suggestionoids = [d['dst'] for d in suggestionoids if d['dst'] not in skip]
        if not suggestionoids:
            return []

        # get just the name and source of found suggestions
        suggestionoids = self.manpage.find({'_id': {'$in': suggestionoids}},
                                           {'name': 1, 'source': 1})
        return [(d.pop('_id'), manpage.from_store_name_only(**d)) for d in suggestionoids]

    def addmapping(self, src: str, dst: Any, score: int) -> None:
        # Python 3: insert_one() instead of insert()
        self.mapping.insert_one({'src': src, 'dst': dst, 'score': score})

    def addmanpage(self, m: manpage) -> manpage:
        '''add m into the store, if it exists first remove it and its mappings

        each man page may have aliases besides the name determined by its
        basename'''
        d = self.manpage.find_one({'source': m.source})
        if d:
            logger.info('removing old manpage %s (%s)', m.source, d['_id'])
            # Python 3: delete_one() instead of remove()
            self.manpage.delete_one({'_id': d['_id']})

            # remove old mappings if there are any
            c = self.mapping.count_documents({})
            # Python 3: delete_many() instead of remove()
            self.mapping.delete_many({'dst': d['_id']})
            c -= self.mapping.count_documents({})
            logger.info('removed %d mappings for manpage %s', c, m.source)

        # Python 3: insert_one() returns InsertOneResult
        result = self.manpage.insert_one(m.to_store())
        o = result.inserted_id

        for alias, score in m.aliases:
            self.addmapping(alias, o, score)
            logger.info('inserting mapping (alias) %s -> %s (%s) with score %d', alias, m.name, o, score)
        return m

    def updatemanpage(self, m: manpage) -> manpage:
        '''update m and add new aliases if necessary

        change updated attribute so we don't overwrite this in the future'''
        logger.info('updating manpage %s', m.source)
        m.updated = True
        # Python 3: update_one() instead of update()
        self.manpage.update_one({'source': m.source}, {'$set': m.to_store()})
        # Python 3: projection parameter instead of fields
        _id = self.manpage.find_one({'source': m.source}, projection={'_id': 1})['_id']
        for alias, score in m.aliases:
            if alias not in self:
                self.addmapping(alias, _id, score)
                logger.info('inserting mapping (alias) %s -> %s (%s) with score %d', alias, m.name, _id, score)
            else:
                logger.debug('mapping (alias) %s -> %s (%s) already exists', alias, m.name, _id)
        return m

    def verify(self) -> Tuple[bool, List[str], List[Any]]:
        # check that everything in manpage is reachable
        mappings = list(self.mapping.find())
        reachable = set([m['dst'] for m in mappings])
        # Python 3: projection parameter instead of fields
        manpages = set([m['_id'] for m in self.manpage.find(projection={'_id': 1})])

        ok = True
        unreachable = manpages - reachable
        if unreachable:
            logger.error('manpages %r are unreachable (nothing maps to them)', unreachable)
            unreachable = [self.manpage.find_one({'_id': u})['name'] for u in unreachable]
            ok = False

        notfound = reachable - manpages
        if notfound:
            logger.error('mappings to inexisting manpages: %r', notfound)
            ok = False

        return ok, unreachable, notfound

    def names(self) -> Iterator[Tuple[Any, str]]:
        # Python 3: projection parameter instead of fields
        cursor = self.manpage.find(projection={'name': 1})
        for d in cursor:
            yield d['_id'], d['name']

    def mappings(self) -> Iterator[Tuple[str, Any]]:
        # Python 3: projection parameter instead of fields
        cursor = self.mapping.find(projection={'src': 1})
        for d in cursor:
            yield d['src'], d['_id']

    def setmulticommand(self, manpageid: Any) -> None:
        # Python 3: update_one() instead of update()
        self.manpage.update_one({'_id': manpageid}, {'$set': {'multicommand': True}})
