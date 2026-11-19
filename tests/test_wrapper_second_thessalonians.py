import importlib.util
from pathlib import Path
import unittest
from unittest import mock


WRAPPER_PATH = Path("/home/kjkim/.local/bin/send_daily_second_thessalonians.py")
PROMPT_PATH = Path("/home/kjkim/.hermes/prompts/daily_second_thessalonians_devotion.txt")
ARCHIVED_REPORT_PATH = Path(
    "/home/kjkim/bible/2026/2Thessalonians/2026-11-20-second-thessalonians-3.md"
)

EXPECTED_HEADINGS = (
    "1. 오늘의 본문",
    "2. 핵심 구절 선정",
    "3. 구조 분석",
    "4. 신학적·복음적 해석",
    "5. 삶 적용 리포트",
    "6. 묵상/기도",
    "7. 한눈에 보는 요약",
)


def _load_wrapper_module():
    spec = importlib.util.spec_from_file_location(
        "send_daily_second_thessalonians", WRAPPER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create module spec for {WRAPPER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestSecondThessaloniansWrapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wrapper = _load_wrapper_module()
        cls.archived_text = ARCHIVED_REPORT_PATH.read_text(encoding="utf-8")

    def _reverted_alias_text(self) -> str:
        self.assertIn("\n6. 묵상/기도\n", self.archived_text)
        reverted = self.archived_text.replace("\n6. 묵상/기도\n", "\n6. 묵상과 기도\n", 1)
        self.assertNotIn("\n6. 묵상/기도\n", reverted)
        self.assertIn("\n6. 묵상과 기도\n", reverted)
        return reverted

    def test_archived_report_with_alias_is_valid(self) -> None:
        reverted = self._reverted_alias_text()
        with mock.patch.object(self.wrapper, "current_chapter", return_value=3):
            self.assertTrue(self.wrapper.is_valid_report(reverted))

    def test_normalize_is_idempotent(self) -> None:
        reverted = self._reverted_alias_text()
        once = self.wrapper.normalize_section_headings(reverted)
        twice = self.wrapper.normalize_section_headings(once)
        self.assertEqual(once, twice)
        self.assertIn("6. 묵상/기도", once)
        self.assertNotIn("6. 묵상과 기도", once)

    def test_diff_debris_rejected(self) -> None:
        polluted = "1. 오늘의 본문\n│ +\n" + self.archived_text
        with mock.patch.object(self.wrapper, "current_chapter", return_value=3):
            self.assertFalse(self.wrapper.is_valid_report(polluted))

    def test_prompt_pins_exact_headings(self) -> None:
        prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
        prompt_lines = [line.strip() for line in prompt_text.splitlines()]
        for heading in EXPECTED_HEADINGS:
            self.assertIn(heading, prompt_lines)
        self.assertIn("6. 묵상/기도", prompt_lines)


if __name__ == "__main__":
    unittest.main()
