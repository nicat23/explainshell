#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/justin/explainshell')

from explainshell import matcher
from tests import helpers

def debug_comsub():
    cmd = "bar $(a)"
    print(f"Command: {cmd}")
    
    s = helpers.mockstore()
    
    # Create a custom matcher to add debug output
    class DebugMatcher(matcher.matcher):
        def visitcommandsubstitution(self, n, command):
            print(f"visitcommandsubstitution called: {n}, {command}")
            result = super().visitcommandsubstitution(n, command)
            print(f"visitcommandsubstitution returning: {result}")
            return result
        
        def visitword(self, n, word):
            print(f"visitword called: {n.pos}, {word}")
            super().visitword(n, word)
    
    m = DebugMatcher(cmd, s)
    groups = m.match()
    
    print(f"\nGroups: {len(groups)}")
    for i, group in enumerate(groups):
        print(f"Group {i} ({group.name}): {len(group.results)} results")
        for j, result in enumerate(group.results):
            print(f"  {j}: {result}")

if __name__ == "__main__":
    debug_comsub()