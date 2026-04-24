import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from debt_scan import scan_text_for_candidates


class DebtScanTest(unittest.TestCase):
    def test_detects_review_needed_comment(self):
        content = "\n".join([
            "public class Sample {",
            "    // TODO: 고객사 확인 후 권한 정책 확정",
            "    public void run() {}",
            "}",
        ])

        candidates = scan_text_for_candidates(
            path="force-app/main/default/classes/Sample.cls",
            content=content,
        )

        self.assertEqual(1, len(candidates))
        self.assertEqual("review-needed", candidates[0].status)
        self.assertEqual("pending-confirm", candidates[0].kind)
        self.assertEqual(2, candidates[0].line)

    def test_detects_hardcoded_salesforce_id(self):
        content = "String accountId = '0015g00000ABCDEFGA';"

        candidates = scan_text_for_candidates(
            path="force-app/main/default/classes/Sample.cls",
            content=content,
        )

        self.assertEqual(1, len(candidates))
        self.assertEqual("code-debt", candidates[0].kind)


if __name__ == "__main__":
    unittest.main()
