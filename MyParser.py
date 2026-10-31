#!/usr/bin/env python3

"""
Program: DECAF20 Parser

Description:
This program reads a DECAF20 source file and checks whether the program
follows the required grammar. The parser receives its tokens from
MyScanner.py and creates a parse tree for valid input.

Run:
    python MyParser.py inputfile.decaf
"""

import sys
import MyScanner

#This dictionary changes the longer token names used by the scanner
#into shorter names that are easier to use inside the parser
TOKEN_NAMES = {
    "T_Int": "INT", "T_Void": "VOID", "T_String": "STRING",
    "T_If": "IF", "T_Else": "ELSE", "T_For": "FOR",
    "T_Return": "RETURN", "T_Print": "PRINT",
    "T_BoolConstant": "BOOL", "T_IDENTIFIER": "ID",
    "T_IntConstant": "INT_CONST",
    "T_STRINGCONSTANT": "STRING_CONST",
    "T_LessEqual": "<=", "T_GreaterEqual": ">=",
    "T_Equal": "==", "T_NotEqual": "!=",
    "T_logicaland": "&&", "T_logicalor": "||"
}


def get_tokens(source):
    #Uses MyScanner.py to scan the source code
    tokens = []

    #Request the token list from the scanner
    for token in MyScanner.scan(source):
        name, text, line, column, end, value = token

        #Use the shorter parser name when one exists
        #Operators and punctuation keep their original text
        kind = TOKEN_NAMES.get(name, text)
        tokens.append((kind, text, line, column))

    #Find the line and column where the file ends
    line = source.count("\n") + 1
    column = len(source.rsplit("\n", 1)[-1]) + 1

    #EOF means end of file
    tokens.append(("EOF", "", line, column))
    return tokens


class ParserError(Exception):
    """
    A custom error used when the parser finds invalid syntax
    The token is saved so the program can later print the correct line and column where the error occurred
    """
    def __init__(self, token):
        self.token = token


class Node:
    """
    Represents one node in the parse tree
    Each node stores a label, an optional line number, and a list of child nodes located below it in the tree
    """
    def __init__(self, label, line=None):
        self.label = label
        self.line = line
        self.children = []

    def add(self, child):
        #Adds a child node to the current parse-tree node
        if child:
            self.children.append(child)

    def print_tree(self, level=0):
        """
        Prints the parse tree using indentation
        The level tells the program how far the node should be indented from the left side
        """
        if level == 0:
            #The Program node does not need a line number
            print(self.label)
        else:
            #Include one space when a node does not have a line number
            if self.line is not None:
                line_field = str(self.line) + " "
            else:
                line_field = " "

            print(line_field + "\t" * level + " " + self.label)

        #Print every child underneath the current node
        for child in self.children:
            child.print_tree(level + 1)


class Parser:
    """
    Recursive-descent parser for DECAF20
    Each parsing method represents one part of the DECAF20 grammar
    The methods call each other as the parser moves through the tokens
    """
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current(self):
        #Returns the token currently being examined
        return self.tokens[self.position]

    def check(self, kind):
        #Checks whether the current token has the expected type
        return self.current()[0] == kind

    def match(self, kind=None):
        """
        Accepts the current token and moves to the next token
        When a token type is provided, the current token must match it
        Otherwise a syntax error is raised
        """
        token = self.current()

        if kind and token[0] != kind:
            raise ParserError(token)

        #Do not move past the EOF token
        if token[0] != "EOF":
            self.position += 1

        return token

    def program(self):
        """
        Parses the complete program
        A DECAF20 program contains zero or more declarations until the parser reaches the end of the file
        """
        node = Node("Program:")

        while not self.check("EOF"):
            node.add(self.declaration())

        return node

    def data_type(self, allow_void=False):
        """
        Parses a data type
        Variables and parameters may use int or string
        A function may also use void as its return type
        """
        types = {"INT", "STRING"}

        if allow_void:
            types.add("VOID")

        if self.current()[0] not in types:
            raise ParserError(self.current())

        return self.match()

    def variable(self, type_token, name, label="VarDecl:"):
        """
        Creates a variable declaration node
        This method is used for global variables, local variables, and function parameters
        """
        node = Node(label, type_token[2])
        node.add(Node("Type: " + type_token[1]))
        node.add(Node("Identifier: " + name[1], name[2]))
        return node

    def declaration(self):
        """
        Parses a global variable or function declaration
        A semicolon after the identifier means it is a variable
        An opening parenthesis means it is a function
        """
        type_token = self.data_type(True)
        name = self.match("ID")

        #A semicolon completes a variable declaration
        if self.check(";"):
            #Variables cannot have the void data type
            if type_token[0] == "VOID":
                raise ParserError(type_token)

            self.match(";")
            return self.variable(type_token, name)

        #A parenthesis begins a function declaration
        if self.check("("):
            return self.function(type_token, name)

        raise ParserError(self.current())

    def function(self, type_token, name):
        """
        Parses a function declaration
        A function contains a return type, identifier, optional parameters, and a statement block for its body
        """
        node = Node("FnDecl:", type_token[2])
        node.add(Node("(return type) Type: " + type_token[1]))
        node.add(Node("Identifier: " + name[1], name[2]))

        #Begin the parameter list
        self.match("(")

        #Continue reading parameters until the closing parenthesis
        while not self.check(")"):
            parameter_type = self.data_type()
            parameter_name = self.match("ID")

            node.add(self.variable(
                parameter_type,
                parameter_name,
                "(formals) VarDecl:"
            ))

            #No comma means the parameter list is finished
            if not self.check(","):
                break

            self.match(",")
            if self.check(")"):
                raise ParserError(self.current())

        self.match(")")

        #Parse the function body
        body = self.block()
        body.label = "(body) StmtBlock:"
        node.add(body)
        return node

    def block(self):
        """
        Parses a block enclosed by braces
        Local variable declarations must appear before the statements inside the block
        """
        self.match("{")
        node = Node("StmtBlock:")

        #Parse local variable declarations
        while self.current()[0] in {"INT", "STRING"}:
            type_token = self.match()
            name = self.match("ID")
            self.match(";")
            node.add(self.variable(type_token, name))

        #Parse statements until the closing brace is found
        while not self.check("}"):
            if self.check("EOF"):
                raise ParserError(self.current())

            node.add(self.statement())

        self.match("}")
        return node

    def statement(self):
        """
        Determines which kind of statement appears next
        A statement may be a block, return statement, print statement, if statement, for statement,
        or expression statement
        """
        if self.check("{"):
            return self.block()

        if self.check("RETURN"):
            return self.return_statement()

        if self.check("PRINT"):
            return self.print_statement()

        if self.check("IF"):
            return self.if_statement()

        if self.check("FOR"):
            return self.for_statement()

        #Any other statement must be an expression followed by a semicolon
        node = self.expression()
        self.match(";")
        return node

    def return_statement(self):
        """
        Parses a return statement
        The expression is optional because a void function may use a return statement without returning a value
        """
        token = self.match("RETURN")
        node = Node("ReturnStmt:", token[2])

        if not self.check(";"):
            node.add(self.expression())

        self.match(";")
        return node

    def print_statement(self):
        """
        Parses a Print statement
        Print must contain at least one expression
        Multiple expressions are separated by commas
        """
        self.match("PRINT")
        self.match("(")
        node = Node("PrintStmt:")

        #Empty parentheses are not valid for Print
        if self.check(")"):
            raise ParserError(self.current())

        while True:
            argument = self.expression()
            argument.label = "(args) " + argument.label.lstrip()
            node.add(argument)

            if not self.check(","):
                break

            self.match(",")
            if self.check(")"):
                raise ParserError(self.current())

        self.match(")")
        self.match(";")
        return node

    def if_statement(self):
        """
        Parses an if statement and its optional else statement
        """
        token = self.match("IF")
        self.match("(")
        node = Node("IfStmt:", token[2])

        #Parse the condition inside the parentheses
        test = self.expression()
        self.match(")")
        test.label = "(test) " + test.label.lstrip()
        node.add(test)

        #Parse the statement executed when the condition is true
        then_part = self.statement()
        then_part.label = "(then) " + then_part.label.lstrip()
        node.add(then_part)

        #Parse the optional else statement
        if self.check("ELSE"):
            self.match("ELSE")
            else_part = self.statement()
            else_part.label = "(else) " + else_part.label.lstrip()
            node.add(else_part)

        return node

    def for_statement(self):
        """
        Parses a for loop
        The loop may contain an initialization expression, condition, update expression, and body statement
        """
        token = self.match("FOR")
        self.match("(")
        node = Node("ForStmt:", token[2])

        #Each tuple contains the ending symbol and parse-tree label for one of the three sections of the for loop
        parts = [
            (";", "(init) "),
            (";", "(test) "),
            (")", "(step) ")
        ]

        for ending, label in parts:
            #A section may be empty
            if not self.check(ending):
                part = self.expression()
                part.label = label + part.label.lstrip()
                node.add(part)

            self.match(ending)

        #Parse the loop body after the closing parenthesis
        body = self.statement()
        body.label = "(body) " + body.label.lstrip()
        node.add(body)
        return node

    def expression(self):
        """
        Parses an expression
        Assignment has the lowest precedence, so binary expressions are processed before checking for
        an assignment operator
        """
        left = self.binary(0)

        if self.check("="):
            operator = self.match("=")

            #The left side of an assignment must be a variable
            if "FieldAccess:" not in left.label:
                raise ParserError(operator)

            node = Node("AssignExpr:", left.line)
            node.add(left)
            node.add(Node("Operator: =", operator[2]))
            node.add(self.expression())
            return node

        return left

    def binary(self, level):
        """
        Parses binary operators by precedence level
        Lower precedence operators appear earlier in the list
        Multiplication, division, and remainder have the highest binary precedence
        """
        levels = [
            ({"||"}, "LogicalExpr:"),
            ({"&&"}, "LogicalExpr:"),
            ({"==", "!="}, "EqualityExpr:"),
            ({"<", ">", "<=", ">="}, "RelationalExpr:"),
            ({"+", "-"}, "ArithmeticExpr:"),
            ({"*", "/", "%"}, "ArithmeticExpr:")
        ]

        #After the final binary level, parse a unary expression
        if level == len(levels):
            return self.unary()

        #Parse operators with higher precedence first
        left = self.binary(level + 1)
        operators, label = levels[level]

        #Continue while operators from this precedence level appear
        while self.current()[0] in operators:
            operator = self.match()
            right = self.binary(level + 1)

            node = Node(label, left.line)
            node.add(left)
            node.add(Node("Operator: " + operator[1], operator[2]))
            node.add(right)
            left = node

        return left

    def unary(self):
        """
        Parses unary logical NOT and unary minus expressions
        """
        if self.current()[0] in {"!", "-"}:
            operator = self.match()

            if operator[0] == "!":
                label = "LogicalExpr:"
            else:
                label = "ArithmeticExpr:"

            node = Node(label, operator[2])
            node.add(Node("Operator: " + operator[1], operator[2]))
            node.add(self.unary())
            return node

        return self.primary()

    def primary(self):
        """
        Parses the smallest parts of an expression
        Primary expressions include constants, identifiers, function calls, array access.
        and expressions inside parentheses
        """
        kind, text, line, column = self.current()

        #Each constant token is matched with its parse tree label
        constants = {
            "INT_CONST": "IntConstant: ",
            "STRING_CONST": "StringConstant: ",
            "BOOL": "BoolConstant: "
        }

        if kind in constants:
            self.match()
            return Node(constants[kind] + text, line)

        if kind == "ID":
            name = self.match()

            #An opening parenthesis after an identifier means a call
            if self.check("("):
                return self.call(name)

            #Otherwise, the identifier represents variable access
            node = Node(" FieldAccess:", line)
            node.add(Node("Identifier: " + text, line))

            #An opening bracket means array access
            if self.check("["):
                self.match("[")
                subscript = self.expression()
                self.match("]")
                subscript.label = "(subscript) " + subscript.label.lstrip()
                node.add(subscript)

            return node

        #Parentheses may be used to group an expression
        if kind == "(":
            self.match("(")
            node = self.expression()
            self.match(")")
            return node

        raise ParserError(self.current())

    def call(self, name):
        """
        Parses a function call
        A function call contains an identifier followed by zero or more arguments inside parentheses
        """
        node = Node(" Call:", name[2])
        node.add(Node("Identifier: " + name[1], name[2]))
        self.match("(")

        while not self.check(")"):
            argument = self.expression()
            argument.label = "(args) " + argument.label.lstrip()
            node.add(argument)

            if not self.check(","):
                break

            self.match(",")
            if self.check(")"):
                raise ParserError(self.current())

        self.match(")")
        return node


def print_error(error, source):
    """
    Prints the syntax error, source line, and a caret showing the location where the parser found the error
    """
    token = error.token
    line = token[2]
    column = token[3]
    lines = source.splitlines()

    #Get the original source line when it exists
    if 1 <= line <= len(lines):
        text = lines[line - 1]
    else:
        text = ""

    print()
    print(f"*** Error line {line}.")
    print(text)
    print(" " * (column - 1) + "^")
    print("*** syntax error")
    print()


def main():
    """
    Opens the input file, receives scanner tokens, runs the parser, and prints either the parse tree or a syntax error
    """
    if len(sys.argv) != 2:
        print("Usage: python MyParser.py inputfile.decaf")
        sys.exit(1)

    try:
        #Read the complete DECAF20 source file
        with open(sys.argv[1], "r", encoding="utf-8") as file:
            source = file.read()

        #Receive the scanner tokens and build the parse tree
        tokens = get_tokens(source)
        tree = Parser(tokens).program()

        print()
        tree.print_tree()

    except (OSError, UnicodeError) as error:
        print("Unable to open input file:", error)
        sys.exit(1)

    except MyScanner.ScannerError as error:
        print(error, file=sys.stderr)
        sys.exit(1)

    except ParserError as error:
        print_error(error, source)
        sys.exit(1)


if __name__ == "__main__":
    main()