import itertools
from operator import itemgetter
from typing import Iterator, List, Callable, Any, TypeVar, Optional

T = TypeVar('T')

def consecutive(l: List[T], fn: Callable[[T], bool]) -> Iterator[List[T]]:
    '''yield consecutive items from l that fn returns True for them

    >>> even = lambda x: x % 2 == 0
    >>> list(consecutive([], even))
    []
    >>> list(consecutive([1], even))
    [[1]]
    >>> list(consecutive([1, 2], even))
    [[1], [2]]
    >>> list(consecutive([2, 4], even))
    [[2, 4]]
    >>> list(consecutive([1, 2, 4], even))
    [[1], [2, 4]]
    >>> list(consecutive([1, 2, 4, 5, 7, 8, 10], even))
    [[1], [2, 4], [5], [7], [8, 10]]
    """
    it = iter(l)
    ll = []
    try:
        while True:
            x = next(it)  # Python 3: next() is a builtin function
            if fn(x):
                ll.append(x)
            else:
                if ll:
                    yield ll
                    ll = []
                yield [x]
    except StopIteration:
        if ll:
            yield ll

def groupcontinuous(l: List[int], key: Optional[Callable[[int], int]] = None) -> Iterator[List[int]]:
    '''
    >>> list(groupcontinuous([1, 2, 4, 5, 7, 8, 10]))
    [[1, 2], [4, 5], [7, 8], [10]]
    >>> list(groupcontinuous(range(5)))
    [[0, 1, 2, 3, 4]]
    """
    if key is None:
        key = lambda x: x
    # Python 3: unpacking in lambda parameters is not supported
    for k, g in itertools.groupby(enumerate(l), lambda item: item[0] - key(item[1])):
        yield list(map(itemgetter(1), g))

def toposorted(graph: List[T], parents: Callable[[T], List[T]]) -> List[T]:
    """
    Returns vertices of a DAG in topological order.

    Arguments:
    graph -- vertices of a graph to be toposorted
    parents -- function (vertex) -> vertices to precede
               given vertex in output
    """
    result = []
    used = set()
    
    def use(v: T, top: T) -> None:
        if id(v) in used:
            return
        for parent in parents(v):
            if parent is top:
                raise ValueError("graph is cyclical", graph)
            use(parent, v)
        used.add(id(v))
        result.append(v)
    
    for v in graph:
        use(v, v)
    return result


def pairwise(iterable):
    """Return successive overlapping pairs taken from the input iterable."""
    # Python 3.10+ has itertools.pairwise, but for compatibility:
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)  # Python 3: zip is an iterator, izip is removed

class peekable:
    '''
    >>> it = peekable(iter('abc'))
    >>> it.index, it.peek(), it.index, it.peek(), next(it), it.index, it.peek(), next(it), next(it), it.index
    (0, 'a', 0, 'a', 'a', 1, 'b', 'b', 'c', 3)
    >>> it.peek()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    StopIteration
    >>> it.peek()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    StopIteration
    >>> next(it)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    StopIteration
    """

    def __init__(self, it):
        self.it = iter(it)
        self._peeked = False
        self._peekvalue = None
        self._idx = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):  # Python 3: __next__ instead of next
        if self._peeked:
            self._peeked = False
            self._idx += 1
            return self._peekvalue
        n = next(self.it)  # Python 3: next() is a builtin function
        self._idx += 1
        return n
    
    def hasnext(self) -> bool:
        try:
            self.peek()
            return True
        except StopIteration:
            return False
    
    def peek(self):
        if self._peeked:
            return self._peekvalue
        else:
            self._peekvalue = next(self.it)  # Python 3: next() is a builtin function
            self._peeked = True
            return self._peekvalue
    
    @property
    def index(self) -> int:
        '''return the index of the next item returned by next()'''
        return self._idx

def namesection(path: str) -> tuple[str, str]:
    assert '.gz' not in path
    name, section = path.rsplit('.', 1)
    return name, section

class propertycache:
    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__

    def __get__(self, obj: Any, type: Optional[type] = None):
        result = self.func(obj)
        self.cachevalue(obj, result)
        return result

    def cachevalue(self, obj: Any, value: Any) -> None:
        setattr(obj, self.name, value)