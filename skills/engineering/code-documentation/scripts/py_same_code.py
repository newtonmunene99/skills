#!/usr/bin/env python3
"""Exit 0 when two Python files differ only in comments and docstrings.

Comments never reach the AST, but docstrings do: they are string expressions
at the top of a module, class or function body. Both files are parsed, leading
docstrings are dropped, and the remaining ASTs are compared, so reformatting
and new or reworded docs pass while any code change fails.

Usage:
  git show HEAD:pkg/mod.py > /tmp/before.py
  python3 scripts/py_same_code.py /tmp/before.py pkg/mod.py
"""

import ast
import sys


def code_only(path: str) -> str:
    """Returns the AST dump of the file at path with every docstring removed."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (
            isinstance(body, list)
            and body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            # A body left empty is the same program as one holding only `pass`.
            node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(f"usage: {sys.argv[0]} BEFORE.py AFTER.py")
    before, after = sys.argv[1], sys.argv[2]
    if code_only(before) != code_only(after):
        sys.exit(f"code changed between {before} and {after}")
    print("only comments and docstrings changed")


if __name__ == "__main__":
    main()
