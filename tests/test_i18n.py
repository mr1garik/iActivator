"""Every user-visible Russian text must have an English and a Ukrainian translation.

Run: python -m unittest discover tests
"""
import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "iactivator"
CYR = re.compile("[Ѐ-ӿ]")
PLACEHOLDER = re.compile(r"\{(\w+)\}")


def _backend_tables():
    tree = ast.parse((PKG / "i18n.py").read_text(encoding="utf-8"))
    tables = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and node.target.id in ("EN", "UK"):
            tables[node.target.id] = ast.literal_eval(node.value)
    return tables["EN"], tables["UK"]


def _js_keys(block: str) -> list:
    """Keys of a JS object literal written as "key": "value" pairs."""
    return [json.loads(m.group(1)) for m in re.finditer(r'("(?:[^"\\]|\\.)*")\s*:', block)]


def _frontend_tables():
    page = (PKG / "page.html").read_text(encoding="utf-8")
    en = page[page.index("const T_EN = {"):page.index("const T_UK = {")]
    uk = page[page.index("const T_UK = {"):]
    uk = uk[:uk.index("\n};") + 3]
    return page, set(_js_keys(en)), set(_js_keys(uk))


class Backend(unittest.TestCase):
    def setUp(self):
        self.en, self.uk = _backend_tables()

    def test_english_and_ukrainian_have_the_same_entries(self):
        self.assertEqual(sorted(set(self.en) - set(self.uk)), [], "missing in UK")
        self.assertEqual(sorted(set(self.uk) - set(self.en)), [], "missing in EN")

    def test_translations_keep_the_placeholders(self):
        for table in (self.en, self.uk):
            for key, value in table.items():
                with self.subTest(key=key):
                    self.assertEqual(sorted(PLACEHOLDER.findall(key)), sorted(PLACEHOLDER.findall(value)))

    def test_english_has_no_cyrillic(self):
        self.assertEqual([v for v in self.en.values() if CYR.search(v)], [])

    def test_every_translated_call_has_an_entry_and_matching_values(self):
        problems = []
        for path in sorted(PKG.glob("*.py")):
            if path.name == "i18n.py":
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id in ("t", "tr", "_check")):
                    continue
                i = 2 if node.func.id == "_check" else 0
                if len(node.args) <= i or not isinstance(node.args[i], ast.Constant) \
                        or not isinstance(node.args[i].value, str):
                    continue
                template = node.args[i].value
                where = f"{path.name}:{node.lineno}"
                if set(PLACEHOLDER.findall(template)) != {k.arg for k in node.keywords}:
                    problems.append(f"{where} values do not match the template: {template[:60]!r}")
                elif CYR.search(template) and template not in self.en:
                    problems.append(f"{where} no translation: {template[:60]!r}")
        self.assertEqual(problems, [])


class Frontend(unittest.TestCase):
    def setUp(self):
        self.page, self.en, self.uk = _frontend_tables()

    def test_english_and_ukrainian_have_the_same_entries(self):
        self.assertEqual(sorted(self.en - self.uk), [], "missing in T_UK")
        self.assertEqual(sorted(self.uk - self.en), [], "missing in T_EN")

    def test_every_T_call_has_an_entry(self):
        script = self.page[self.page.index("function T(s)"):]
        used = {json.loads(m.group(1)) for m in re.finditer(r'\bT\(("(?:[^"\\]|\\.)*")\)', script)}
        self.assertEqual(sorted(k for k in used if CYR.search(k) and k not in self.en), [])


if __name__ == "__main__":
    unittest.main()
