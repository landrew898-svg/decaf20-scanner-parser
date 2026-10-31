# DECAF20 Scanner and Parser

A small Python language-processing project with a lexical scanner and a recursive-descent parser. The scanner identifies tokens and their source locations; the parser checks syntax and prints an indented syntax tree.

## Features

- Integer and string declarations, functions, parameters, and calls
- Assignments, return statements, and `Print` statements
- `if` / `else` and `for` statements
- Arithmetic, comparison, and logical expressions with operator precedence
- Line and column tracking, comments, and lexical/syntax error reporting

## Run

Requires Python 3.8 or newer. No third-party packages are needed. Run from the repository root:

```sh
python MyScanner.py examples/t1.decaf
python MyParser.py examples/t1.decaf
```

The scanner prints token names, lexemes, and source locations. The parser prints a tree rooted at `Program:`. Invalid input exits with status 1:

```sh
python MyParser.py examples/bad1.decaf
python MyParser.py examples/bad3.decaf
```

`bad1.decaf` omits a parameter name. `bad3.decaf` omits a semicolon after `Print(a)`. Syntax errors point at the token where parsing fails, which can follow the actual mistake.

## Example

```c
void main() {
  int result;
  result = 2 + 3 * 4;
  Print(result);
}
```

This is parsed into declarations, an assignment, and a print statement. Multiplication groups more tightly than addition. The program does not calculate or print `14`; it describes the source structure.

## Checks

```sh
python -B -m unittest discover -s tests -v
```

The regression checks cover the included examples, scanner output, expression precedence, control flow, malformed tokens, comma handling, and command-line exit codes.

## Scope and limitations

This is an educational scanner/parser, not a complete compiler or interpreter. It does not generate code, execute programs, check types, or resolve names. For example, it can parse a call to an undefined function. Array indexing is recognized in expressions, but array declarations are not implemented. There are no classes or `while` statements, and only decimal integer literals are supported. Parsing stops at the first error. Very deeply nested input may hit Python's recursion limit.

The repository contains a cleaned-up version of an earlier implementation. Cleanup fixes standalone scanner recursion, reports unfinished strings/comments and unknown characters as lexical errors, corrects end-of-file locations, and rejects trailing commas in parameter and argument lists. Full conformance to an external DECAF20 grammar has not been verified.
