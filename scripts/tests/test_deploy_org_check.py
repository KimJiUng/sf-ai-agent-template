import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from deploy_org_check import merge_non_overlapping_changes


class MergeNonOverlappingChangesTest(unittest.TestCase):
    def test_merges_separate_method_changes(self):
        base = "\n".join([
            "public class Sample {",
            "    public void methodA() {",
            "        Integer value = 1;",
            "    }",
            "}",
            "",
        ])
        local = "\n".join([
            "public class Sample {",
            "    public void methodA() {",
            "        Integer value = 2;",
            "    }",
            "}",
            "",
        ])
        org = "\n".join([
            "public class Sample {",
            "    public void methodA() {",
            "        Integer value = 1;",
            "    }",
            "",
            "    public void methodB() {",
            "        Integer value = 3;",
            "    }",
            "}",
            "",
        ])

        result = merge_non_overlapping_changes(base, local, org)

        self.assertTrue(result.success)
        self.assertIn("Integer value = 2;", result.content)
        self.assertIn("public void methodB()", result.content)
        self.assertEqual([], result.conflicts)

    def test_reports_conflict_for_same_method_changes(self):
        base = "\n".join([
            "public class Sample {",
            "    public void methodA() {",
            "        Integer value = 1;",
            "    }",
            "}",
            "",
        ])
        local = base.replace("Integer value = 1;", "Integer value = 2;")
        org = base.replace("Integer value = 1;", "Integer value = 3;")

        result = merge_non_overlapping_changes(base, local, org)

        self.assertFalse(result.success)
        self.assertTrue(result.conflicts)


if __name__ == "__main__":
    unittest.main()
