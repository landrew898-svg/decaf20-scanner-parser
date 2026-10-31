#!/usr/bin/env python3

"""
Program: DECAF20 Scanner

Description:
This program implements a lexical scanner for the DECAF20 language.
It reads a DECAF20 source file, identifies lexemes, classifies them
into their corresponding tokens, and prints each token along with its
line and column location in the required format.
"""

import sys


class ScannerError(Exception):
    """A lexical error with a source location."""

    def __init__(self, message, line, column):
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, column {column}: {message}")

#Reserved keywords in DECAF20
#If one of these words is found, it is assigned its predefined
#token instead of being treated as a normal identifier
KEYWORDS = {
    "int": "T_Int",
    "void": "T_Void",
    "string": "T_String",
    "if": "T_If",
    "else": "T_Else",
    "for": "T_For",
    "return": "T_Return",
    "Print": "T_Print",
}

#Boolean values are constants, not identifiers
BOOL_CONSTANTS = {"true", "false"}

#Operators made of two characters must be checked before one character tokens
TWO_CHAR_TOKENS = {
    "<=": "T_LessEqual",
    ">=": "T_GreaterEqual",
    "==": "T_Equal",
    "!=": "T_NotEqual",
    "&&": "T_logicaland",
    "||": "T_logicalor",
}

#Single character punctuation and operators
#The expected output prints these tokens using the character itself like '(' or '+'
ONE_CHAR_TOKENS = set("(){}[];,+-*/%=<>!")


def print_token(lexeme, line, start_col, end_col, token_name, value=None):
    """
    Prints one token using the same format as the sample expected outputs

    lexeme: the exact text found in the source file
    line: line number where the token appears
    start_col/end_col: starting and ending column numbers
    token_name: token type
    value: optional value for constants
    """
    if value is None:
        print(f"{lexeme}     line {line} Cols  {start_col} - {end_col}  is  {token_name} ")
    else:
        print(f"{lexeme}     line {line} Cols  {start_col} - {end_col}  is  {token_name} (value= {value})")


def scan(source, display=False):
    """
    Scans the complete source file and prints each token found

    Variable i is the current index in the source string
    Variables line and col track the current position for the output
    """
    #Initialize the scanner's current position
    #i keeps track of the current character in the source code
    #line and col are used to report where each token was found
    i = 0
    line = 1
    col = 1
    n = len(source)

    #Store every token so the parser can use the scanner's output
    tokens = []

    #Save each token and print it only when display is True
    def add_token(lexeme, token_line, start_col, end_col,
                  token_name, value=None):
        tokens.append((token_name, lexeme, token_line,
                       start_col, end_col, value))

        if display:
            print_token(lexeme, token_line, start_col,
                        end_col, token_name, value)

    #Continue scanning until every character in the source file has been processed
    while i < n:
        ch = source[i]

        #Ignore whitespace because it separates tokens
        if ch in " \t\r":
            i += 1
            col += 1
            continue

        #A newline marks the beginning of a new source line
        #Reset the column counter so future tokens have the correct location
        if ch == "\n":
            i += 1
            line += 1
            col = 1
            continue

        #Skip single line comments
        #Everything from // to the end of the line is ignored by the scanner
        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            i += 2
            col += 2

            #Continue moving forward until the end of the current line
            while i < n and source[i] != "\n":
                i += 1
                col += 1
            continue

        #Skip block comments because they can span multiple lines
        #line and column numbers must be updated while moving through the comment
        if ch == "/" and i + 1 < n and source[i + 1] == "*":
            start_line, start_col = line, col
            closed = False
            i += 2
            col += 2

            #Continue scanning until the closing */ is found
            while i < n - 1:

                #End of block comment
                if source[i] == "*" and source[i + 1] == "/":
                    i += 2
                    col += 2
                    closed = True
                    break

                #Keep line/column tracking correct inside multi line comments
                if source[i] == "\n":
                    i += 1
                    line += 1
                    col = 1
                else:
                    i += 1
                    col += 1
            if not closed:
                raise ScannerError("Unterminated block comment", start_line, start_col)
            continue

        #String constants start and end with double quotes
        #Escaped characters like \n are kept in the same string token
        if ch == '"':
            start_line = line
            start_col = col
            lexeme = ch
            closed = False
            i += 1
            col += 1

            #Continue scanning until every character in the source file has been processed
            while i < n:
                c = source[i]
                if c in "\n\r":
                    raise ScannerError("Unterminated string", start_line, start_col)
                lexeme += c
                i += 1
                col += 1

                #If a backslash is found, include the next character too
                if c == "\\" and i < n:
                    if source[i] in "\n\r":
                        raise ScannerError("Unterminated string", start_line, start_col)
                    lexeme += source[i]
                    i += 1
                    col += 1
                    continue

                #Closing quote marks the end of the string constant
                if c == '"':
                    closed = True
                    break

            if not closed:
                raise ScannerError("Unterminated string", start_line, start_col)
            add_token(lexeme, start_line, start_col, col - 1,
                        "T_STRINGCONSTANT", lexeme)
            continue

        #Identifiers and keywords begin with a letter or underscore
        #After the first character, they can contain letters, digits, or underscores
        if ch.isalpha() or ch == "_":
            start_col = col
            start_i = i

            #Continue collecting characters while they are valid identifier characters
            while i < n and (source[i].isalnum() or source[i] == "_"):
                i += 1
                col += 1

            lexeme = source[start_i:i]
            end_col = col - 1

            #Decide whether the word is a boolean constant, keyword, or normal identifier
            #This order matters because reserved words should not be printed as identifiers
            if lexeme in BOOL_CONSTANTS:
                add_token(lexeme, line, start_col, end_col,
                            "T_BoolConstant", lexeme)
            elif lexeme in KEYWORDS:
                add_token(lexeme, line, start_col, end_col,
                            KEYWORDS[lexeme])
            else:
                add_token(lexeme, line, start_col, end_col,
                            "T_IDENTIFIER")
            continue

        #Integer constants are one or more digits in a row
        if ch.isdigit():
            start_col = col
            start_i = i

            #Continue reading digits until the complete integer constant has been collected
            while i < n and source[i].isdigit():
                i += 1
                col += 1

            lexeme = source[start_i:i]
            add_token(lexeme, line, start_col, col - 1,
                        "T_IntConstant", lexeme)
            continue

        #Check two character operators before one character tokens so operators
        #such as <=, !=, and && are not split incorrectly
        if i + 1 < n and source[i:i + 2] in TWO_CHAR_TOKENS:
            lexeme = source[i:i + 2]
            add_token(lexeme, line, col, col + 1, TWO_CHAR_TOKENS[lexeme])
            i += 2
            col += 2
            continue

        #If the current character is a valid punctuation symbol or operator, print it as a token
        if ch in ONE_CHAR_TOKENS:
            add_token(ch, line, col, col, f"'{ch}'")
            i += 1
            col += 1
            continue

        #If an unexpected character appears, print it as unknown and move on
        #Prevents the scanner from getting stuck in an infinite loop
        raise ScannerError(f"Unexpected character {ch!r}", line, col)

    #Return the tokens so MyParser.py can process them
    return tokens

def main():

    #Main function
    #Makes sure the user supplied an input file, reads the file into memory,
    #and starts the scanner
    if len(sys.argv) != 2:
        print("Usage: python MyScanner.py <source-file.decaf>", file=sys.stderr)
        sys.exit(1)

    try:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            source_code = f.read()
        scan(source_code, display=True)
    except (OSError, UnicodeError, ScannerError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
