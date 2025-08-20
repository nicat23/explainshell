#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/justin/explainshell')

import bashlex
from explainshell import matcher
from tests import helpers

def debug_ast():
    cmd = "bar $(a) -b \"b $(c) `c`\" '$(d)' >$(e) `f`"
    print(f"Command: {cmd}")
    
    # Parse with bashlex to see the AST
    ast = bashlex.parse(cmd)
    print(f"AST: {ast}")
    
    # Print AST structure
    def print_node(node, indent=0):
        prefix = "  " * indent
        print(f"{prefix}{node.kind}: {getattr(node, 'word', '')} pos={getattr(node, 'pos', None)}")
        if hasattr(node, 'list'):
            for child in node.list:
                print_node(child, indent + 1)
        if hasattr(node, 'parts'):
            for part in node.parts:
                print_node(part, indent + 1)
    
    print("\nAST Structure:")
    for node in ast:
        print_node(node)
    
    # Now test the matcher
    s = helpers.mockstore()
    m = matcher.matcher(cmd, s)
    groups = m.match()
    
    print(f"\nGroups: {len(groups)}")
    for i, group in enumerate(groups):
        print(f"Group {i} ({group.name}): {len(group.results)} results")
        for j, result in enumerate(group.results):
            print(f"  {j}: {result}")

if __name__ == "__main__":
    debug_ast()