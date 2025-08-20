#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/justin/explainshell')

from explainshell import matcher
from tests import helpers

def debug_redirect():
    cmd = "bar >$(e)"
    print(f"Command: {cmd}")
    
    s = helpers.mockstore()
    m = matcher.matcher(cmd, s)
    groups = m.match()
    
    print(f"\nGroups: {len(groups)}")
    for i, group in enumerate(groups):
        print(f"Group {i} ({group.name}): {len(group.results)} results")
        for j, result in enumerate(group.results):
            print(f"  {j}: {result}")

if __name__ == "__main__":
    debug_redirect()