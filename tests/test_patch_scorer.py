import pytest
import json
from pathlib import Path
from eval.patch_score.scorer import score_patches

@pytest.fixture
def workspace(tmp_path):
    st_dir = tmp_path / "source_tree"
    st_dir.mkdir()
    diff_dir = tmp_path / "diffs"
    diff_dir.mkdir()
    
    sample_c = st_dir / "sample.c"
    sample_c.write_text("""
void foo() {
    int a = 1;
}

int bar(int a, int b) {
    int c = a + b;
    // do something
    return c;
}
""")
    
    other_c = st_dir / "other.c"
    other_c.write_text("void baz() {}\n")

    ref_diff = diff_dir / "ref.diff"
    ref_diff.write_text("""--- a/sample.c
+++ b/sample.c
@@ -7,2 +7,2 @@
-    // do something
+    // patched
""")

    cand_same = diff_dir / "cand_same.diff"
    cand_same.write_text("""--- a/sample.c
+++ b/sample.c
@@ -7,2 +7,2 @@
-    // do something
+    // perfectly patched
""")

    cand_wrong = diff_dir / "cand_wrong.diff"
    cand_wrong.write_text("""--- a/other.c
+++ b/other.c
@@ -1,1 +1,2 @@
 void baz() {}
+int extra = 1;
""")

    cand_overbroad = diff_dir / "cand_overbroad.diff"
    cand_overbroad.write_text("""--- a/sample.c
+++ b/sample.c
@@ -7,2 +7,12 @@
-    // do something
+    // patched
+    if (a < 0) return 0;
+    if (b < 0) return 0;
+    if (c < 0) return 0;
+    if (a > 10) return 0;
+    if (b > 10) return 0;
+    c = c + 0;
+    c = c - 0;
+    c = c * 1;
+    c = c / 1;
""")

    return st_dir, ref_diff, cand_same, cand_wrong, cand_overbroad

def test_score_strong_match(workspace):
    st_dir, ref_diff, cand_same, _, _ = workspace
    score = score_patches(cand_same, ref_diff, st_dir)
    assert score.verdict.label == "strong_match"
    assert score.overlap["same_file"] is True
    assert score.overlap["same_function"] is True
    assert score.locality["function_mapping_status"] == "mapped"
    assert score.minimality["minimality_label"] == "tight"
    
    # Test JSON output deterministic sort
    js = json.loads(score.to_json())
    assert "low_line_overlap" not in js["verdict"]["failure_taxonomy"]

def test_score_wrong_file(workspace):
    st_dir, ref_diff, _, cand_wrong, _ = workspace
    score = score_patches(cand_wrong, ref_diff, st_dir)
    assert score.verdict.label == "wrong_file"
    assert "wrong_file" in score.verdict.failure_taxonomy

def test_score_overbroad(workspace):
    st_dir, ref_diff, _, _, cand_overbroad = workspace
    score = score_patches(cand_overbroad, ref_diff, st_dir)
    assert score.verdict.label == "over_broad"
    assert "over_broad" in score.verdict.failure_taxonomy
    assert score.minimality["minimality_label"] == "sprawling"

def test_parse_error(workspace):
    st_dir, ref_diff, _, _, _ = workspace
    bad_diff = st_dir / "bad.diff" # Doesn't exist
    score = score_patches(bad_diff, ref_diff, st_dir)
    assert score.verdict.label == "parse_error"

def test_fallback_unmapped_strong_match(workspace):
    st_dir, ref_diff, _, _, _ = workspace
    unmapped_c = st_dir / "unmapped.c"
    unmapped_c.write_text("""
int unmapped_trick = (1);
{
    int a = 1;
    // do something
    return a;
}
""")
    
    ref_diff = st_dir.parent / "diffs" / "ref_unmapped.diff"
    ref_diff.write_text("""--- a/unmapped.c
+++ b/unmapped.c
@@ -4,2 +4,2 @@
-    // do something
+    // perfectly patched
""")

    cand_same = st_dir.parent / "diffs" / "cand_unmapped.diff"
    cand_same.write_text("""--- a/unmapped.c
+++ b/unmapped.c
@@ -4,2 +4,2 @@
-    // do something
+    // perfectly patched
""")

    score = score_patches(cand_same, ref_diff, st_dir)
    assert score.verdict.label == "strong_match"
    assert score.locality["function_mapping_status"] == "unmapped_both"
    assert "wrong_function" not in score.verdict.failure_taxonomy

def test_wrong_function_same_file(workspace):
    st_dir, ref_diff, _, _, _ = workspace
    
    cand_wrong_func = st_dir.parent / "diffs" / "cand_wrong_func.diff"
    cand_wrong_func.write_text("""--- a/sample.c
+++ b/sample.c
@@ -2,2 +2,2 @@
 void foo() {
-    int a = 1;
+    int a = 2;
 }
""")
    
    score = score_patches(cand_wrong_func, ref_diff, st_dir)
    assert score.verdict.label == "wrong_function"
    assert "wrong_function" in score.verdict.failure_taxonomy
    assert score.locality["function_mapping_status"] == "mapped"
