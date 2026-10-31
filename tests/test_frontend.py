import contextlib
import io
from pathlib import Path
import subprocess
import sys
import unittest

import MyParser
import MyScanner


ROOT = Path(__file__).resolve().parents[1]


def parse(source):
    return MyParser.Parser(MyParser.get_tokens(source)).program()


class FrontendTests(unittest.TestCase):
    def test_included_valid_example(self):
        tree = parse((ROOT / 'examples/t1.decaf').read_text())
        self.assertEqual(len(tree.children), 4)

    def test_included_invalid_examples(self):
        for name in ['bad1.decaf', 'bad3.decaf']:
            with self.subTest(name=name), self.assertRaises(MyParser.ParserError):
                parse((ROOT / 'examples' / name).read_text())

    def test_scanner_display_and_locations(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            tokens = MyScanner.scan('// comment\nint x;', display=True)
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0][:5], ('T_Int', 'int', 2, 1, 3))
        self.assertIn('T_Int', output.getvalue())

    def test_malformed_tokens(self):
        for source in ['"unfinished', '/* unfinished', '/*', '@', '"line\nbreak"', '"escape\\\nline"']:
            with self.subTest(source=source), self.assertRaises(MyScanner.ScannerError):
                MyScanner.scan(source)

    def test_closed_comments_and_escaped_strings(self):
        tokens = MyScanner.scan('/* comment */ "a\\"b"')
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0][0], 'T_STRINGCONSTANT')

    def test_trailing_commas(self):
        for source in ['void f(int x,) {}', 'void f() { g(1,); }', 'void f() { Print(1,); }']:
            with self.subTest(source=source), self.assertRaises(MyParser.ParserError):
                parse(source)

    def test_precedence(self):
        tree = parse('int f() { return 1 + 2 * 3; }')
        expr = tree.children[0].children[-1].children[0].children[0]
        self.assertEqual(expr.children[1].label, 'Operator: +')
        self.assertEqual(expr.children[2].children[1].label, 'Operator: *')

    def test_control_flow(self):
        parse('void f() { int x; for (x = 0; x < 3; x = x + 1) { if (x == 1) Print(x); else Print(0); } }')

    def test_eof_location(self):
        self.assertEqual(MyParser.get_tokens('int x;\n')[-1], ('EOF', '', 2, 1))

    def test_cli(self):
        for script, args, expected in [
            ('MyScanner.py', ['examples/t1.decaf'], 0),
            ('MyParser.py', ['examples/t1.decaf'], 0),
            ('MyParser.py', ['examples/bad1.decaf'], 1),
            ('MyParser.py', ['examples/bad3.decaf'], 1),
            ('MyScanner.py', ['missing.decaf'], 1),
            ('MyParser.py', ['missing.decaf'], 1),
            ('MyScanner.py', [], 1),
            ('MyParser.py', [], 1),
        ]:
            with self.subTest(script=script, args=args):
                result = subprocess.run([sys.executable, '-B', script, *args], cwd=ROOT,
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, expected)
                self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
