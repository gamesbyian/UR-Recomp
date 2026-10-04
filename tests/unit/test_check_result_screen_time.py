import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_result_screen_time as chk  # noqa: E402


class ResultScreenTimeTests(unittest.TestCase):
    def test_time_tokens_only(self) -> None:
        texts = ["DRAGSTER", "PLAYER     TIME", "MIKE", "0:28.56", "SOMEONE", "NO TIME"]
        self.assertEqual(chk.finish_times(texts), ["0:28.56"])

    def test_blank_time_row_is_detected(self) -> None:
        texts = ["DRAGSTER", "PLAYER     TIME", "MIKE", "SOMEONE", "NO TIME"]
        self.assertEqual(chk.finish_times(texts), [])


if __name__ == "__main__":
    unittest.main()
