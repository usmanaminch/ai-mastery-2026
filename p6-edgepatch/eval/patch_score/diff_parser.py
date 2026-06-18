"""
Diff Parser for EdgePatch Evaluation.
Safely parses unified diffs without shelling out to the system.
Extracts hunks, line mappings, and file paths.
"""
import re
from pathlib import Path
from typing import List, Optional
from .models import DiffLine, DiffHunk, FileDiff

def parse_diff_text(diff_text: str) -> List[FileDiff]:
    file_diffs: List[FileDiff] = []
    current_diff: Optional[FileDiff] = None
    current_hunk: Optional[DiffHunk] = None
    
    old_line_tracker = 0
    new_line_tracker = 0

    lines = diff_text.splitlines()
    idx = 0
    
    while idx < len(lines):
        line = lines[idx]
        
        if line.startswith("diff --git"):
            # New file diff starting
            pass
        elif line.startswith("--- "):
            old_path = line[4:].strip().split('\t')[0]
            if old_path.startswith("a/"):
                old_path = old_path[2:]
            
            idx += 1
            if idx < len(lines) and lines[idx].startswith("+++ "):
                new_path = lines[idx][4:].strip().split('\t')[0]
                if new_path.startswith("b/"):
                    new_path = new_path[2:]
                
                is_new = old_path == "/dev/null"
                is_deleted = new_path == "/dev/null"
                
                # Sanitize paths
                old_name = new_path if is_new else old_path
                new_name = old_path if is_deleted else new_path
                
                current_diff = FileDiff(
                    old_path=old_name,
                    new_path=new_name,
                    is_new=is_new,
                    is_deleted=is_deleted
                )
                file_diffs.append(current_diff)
                current_hunk = None
        
        elif line.startswith("@@ ") and current_diff is not None:
            # @@ -old_start,old_count +new_start,new_count @@
            match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if match:
                o_start = int(match.group(1))
                o_count = int(match.group(2)) if match.group(2) else 1
                n_start = int(match.group(3))
                n_count = int(match.group(4)) if match.group(4) else 1
                
                current_hunk = DiffHunk(o_start, o_count, n_start, n_count)
                current_diff.hunks.append(current_hunk)
                
                old_line_tracker = o_start
                new_line_tracker = n_start
                
        elif current_hunk is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk.lines.append(DiffLine(0, new_line_tracker, line[1:], "added"))
                current_diff.added_lines += 1
                current_diff.changed_new_line_numbers.append(new_line_tracker)
                new_line_tracker += 1
            elif line.startswith("-") and not line.startswith("---"):
                current_hunk.lines.append(DiffLine(old_line_tracker, 0, line[1:], "removed"))
                current_diff.removed_lines += 1
                current_diff.changed_old_line_numbers.append(old_line_tracker)
                old_line_tracker += 1
            elif line.startswith(" "):
                current_hunk.lines.append(DiffLine(old_line_tracker, new_line_tracker, line[1:], "context"))
                old_line_tracker += 1
                new_line_tracker += 1
            elif line == "" or line == "\\ No newline at end of file":
                pass
            else:
                # Malformed line or end of hunk
                current_hunk = None
        
        idx += 1

    return file_diffs

def parse_diff_file(diff_path: Path) -> List[FileDiff]:
    try:
        content = diff_path.read_text(encoding="utf-8")
        return parse_diff_text(content)
    except Exception:
        raise ValueError(f"Failed to parse diff file {diff_path}")
