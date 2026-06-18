import pytest
from pathlib import Path
from eval.patch_score.diff_parser import parse_diff_text

def test_parse_simple_diff():
    diff_text = """diff --git a/sample.c b/sample.c
--- a/sample.c
+++ b/sample.c
@@ -10,3 +10,3 @@
 context1
-old_line
+new_line
 context2
"""
    diffs = parse_diff_text(diff_text)
    assert len(diffs) == 1
    assert diffs[0].old_path == "sample.c"
    assert diffs[0].new_path == "sample.c"
    assert diffs[0].added_lines == 1
    assert diffs[0].removed_lines == 1
    assert diffs[0].changed_old_line_numbers == [11]
    assert diffs[0].changed_new_line_numbers == [11]

def test_parse_deleted_file():
    diff_text = """--- a/sample.c
+++ /dev/null
@@ -1,2 +0,0 @@
-del1
-del2
"""
    diffs = parse_diff_text(diff_text)
    assert len(diffs) == 1
    assert diffs[0].is_deleted is True
    assert diffs[0].removed_lines == 2
    assert diffs[0].added_lines == 0
