# AST wrapper class for pycparser.c_ast

import io
import re

import pycparser

class ParseError(Exception):
    pass

class AST():
    # string string [pycparser.c_parser.CParser] -> AST
    def __init__(self, predicate, parser=None):
        """Parses funname(predicate) into Abstract Syntax Tree
        :parser: will be instantiated as a CParser if it doesn't exist.
        Raises ParseError if parsing fails.
        """
        snippet = r"void func() {{ ({pred}); }}".format(pred=predicate)
        parser = parser if parser else pycparser.c_parser.CParser()
        self.ast = parse_assertion(snippet, parser)

    def __str__(self):
        buf = io.StringIO()
        self.ast.show(buf=buf)
        return buf.getvalue()

# string pycparser.c_parser.CParser [Boolean] -> pycparser.c_ast
def parse_assertion(snippet, parser, num_attempts=0):
    try:
        ast = parser.parse(snippet)
        func_decl = ast.ext[-1] # last item in case preceded by typedefs
        func_body = func_decl.body
        assertion_ast = func_body.block_items[0]
        return assertion_ast
    except pycparser.plyparser.ParseError as err:
        # error may be caused by unknown types. Attempt to find them
        # and define them.
        unknown_types = set()
        if num_attempts == 0:
            # offsetof(S, x) fails (unless S is typedeffed, or preceded by 'struct')
            unknown_types = get_offsetters(snippet)
        elif num_attempts == 1:
            unknown_types = get_type_casters(snippet)
        else:
            raise ParseError(str(err))

        snippet = add_typdefs(unknown_types, snippet)
        return parse_assertion(snippet, parser, num_attempts+1)

def get_offsetters(snippet):
    """String -> {String}"""
    offsetof_pattern = r"\boffsetof\s*\(\s*(\w+)\s*,"
    types = re.findall(offsetof_pattern, snippet)
    types = {t for t in types} # remove duplicates
    return types

# String -> {String}
def get_type_casters(snippet):
    type_cast_pattern = r"[^\w]\( *(\w+)( *\**)?\)"
    types = re.findall(type_cast_pattern, snippet)
    types = {t for t,_ in types} # remove duplicates
    return types


# {string} string -> string
def add_typdefs(types, snippet):
    """Prepend snippet with typdefs. Only works if types is a set"""
    for t in types:
        snippet = r"typedef int {t}; {s}".format(t=t, s=snippet)
    return snippet


