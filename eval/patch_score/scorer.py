"""
Patch Scorer for EdgePatch Evaluation.
Calculates locality and minimality proxy signals to determine patch quality.
"""
from pathlib import Path
from typing import List, Set, Tuple, Dict, Any
from .models import PatchScore, Verdict, PatchFootprint, FileDiff
from .diff_parser import parse_diff_file
from .source_map import map_changed_lines

def build_footprint(diffs: List[FileDiff], source_tree: Path) -> Tuple[PatchFootprint, Set[str]]:
    fp = PatchFootprint()
    touched_line_keys: Set[str] = set()
    funcs_set: Set[str] = set()
    
    for d in diffs:
        file_path = d.new_path if not d.is_deleted else d.old_path
        fp.files.append(file_path)
        fp.added_lines += d.added_lines
        fp.removed_lines += d.removed_lines
        
        all_changed = sorted(list(set(d.changed_old_line_numbers + d.changed_new_line_numbers)))
        fp.lines_touched += len(all_changed)
        
        if all_changed:
            fp.line_ranges.append(f"{file_path}:{all_changed[0]}-{all_changed[-1]}")
            
        for ln in all_changed:
            touched_line_keys.add(f"{file_path}:{ln}")
            
        target_file = source_tree / file_path
        if target_file.exists() and not d.is_deleted:
            code = target_file.read_text(encoding="utf-8")
            touched_funcs = map_changed_lines(code, all_changed)
            for f in touched_funcs:
                funcs_set.add(f"{file_path}:{f}")
    
    fp.files = sorted(list(set(fp.files)))
    fp.functions = sorted(list(funcs_set))
    return fp, touched_line_keys

def _parse_error_score() -> PatchScore:
    return PatchScore(
        verdict=Verdict(
            label="parse_error",
            confidence=0.0,
            explanation="Failed to parse diff or source maps.",
            failure_taxonomy=["parse_error"]
        )
    )

def score_patches(candidate_diff: Path, reference_diff: Path, source_tree: Path) -> PatchScore:
    try:
        cand_diffs = parse_diff_file(candidate_diff)
        ref_diffs = parse_diff_file(reference_diff)
    except Exception:
        return _parse_error_score()

    cand_fp, cand_lines = build_footprint(cand_diffs, source_tree)
    ref_fp, ref_lines = build_footprint(ref_diffs, source_tree)

    cand_files_set = set(cand_fp.files)
    ref_files_set = set(ref_fp.files)
    same_file = bool(cand_files_set.intersection(ref_files_set))

    cand_funcs_set = set(cand_fp.functions)
    ref_funcs_set = set(ref_fp.functions)
    same_function = bool(cand_funcs_set.intersection(ref_funcs_set))

    ref_lines_len = max(len(ref_lines), 1)
    line_overlap_ratio = len(cand_lines.intersection(ref_lines)) / ref_lines_len
    
    ref_funcs_len = max(len(ref_funcs_set), 1)
    func_overlap_ratio = len(cand_funcs_set.intersection(ref_funcs_set)) / ref_funcs_len

    cand_changed = cand_fp.added_lines + cand_fp.removed_lines
    ref_changed = ref_fp.added_lines + ref_fp.removed_lines
    minimality_ratio = cand_changed / max(ref_changed, 1)

    if minimality_ratio <= 1.25:
        min_label = "tight"
    elif minimality_ratio <= 2.0:
        min_label = "acceptable"
    elif minimality_ratio <= 4.0:
        min_label = "broad"
    else:
        min_label = "sprawling"

    if same_file and same_function and line_overlap_ratio > 0:
        locality_score = 1.0
    elif same_file and same_function and line_overlap_ratio == 0:
        locality_score = 0.8
    elif same_file and not same_function:
        locality_score = 0.5
    else:
        locality_score = 0.0

    overlap_score = (line_overlap_ratio + func_overlap_ratio) / 2.0
    confidence = round((0.6 * locality_score) + (0.4 * overlap_score), 3)

    verdict_label = ""
    taxonomy = []
    
    if not same_file:
        verdict_label = "wrong_file"
        taxonomy.append("wrong_file")
    elif not same_function:
        verdict_label = "wrong_function"
        taxonomy.append("wrong_function")
    elif same_file and same_function and min_label == "sprawling":
        verdict_label = "over_broad"
        taxonomy.append("over_broad")
    elif minimality_ratio < 0.5 and line_overlap_ratio < 0.3:
        verdict_label = "under_broad"
        taxonomy.append("under_broad")
    elif same_file and same_function and min_label == "broad" and line_overlap_ratio >= 0.3:
        verdict_label = "acceptable_broader"
    elif same_file and same_function and line_overlap_ratio >= 0.3 and min_label in ["tight", "acceptable"]:
        verdict_label = "strong_match"
    else:
        if cand_changed < ref_changed:
            verdict_label = "under_broad"
            taxonomy.append("under_broad")
        else:
            verdict_label = "acceptable_broader"

    if line_overlap_ratio < 0.3 and "low_line_overlap" not in taxonomy:
        taxonomy.append("low_line_overlap")

    score = PatchScore(
        locality={
            "files_touched_by_candidate": cand_fp.files,
            "files_touched_by_reference": ref_fp.files,
            "functions_touched_by_candidate": cand_fp.functions,
            "functions_touched_by_reference": ref_fp.functions,
            "line_ranges_touched_by_candidate": cand_fp.line_ranges,
            "line_ranges_touched_by_reference": ref_fp.line_ranges,
            "stayed_in_region": same_file and same_function
        },
        minimality={
            "candidate_lines_added": cand_fp.added_lines,
            "candidate_lines_removed": cand_fp.removed_lines,
            "candidate_total_changed": cand_changed,
            "reference_lines_added": ref_fp.added_lines,
            "reference_lines_removed": ref_fp.removed_lines,
            "reference_total_changed": ref_changed,
            "minimality_ratio": round(minimality_ratio, 3),
            "minimality_label": min_label
        },
        overlap={
            "same_file": same_file,
            "same_function": same_function,
            "line_overlap_ratio": round(line_overlap_ratio, 3),
            "function_overlap_ratio": round(func_overlap_ratio, 3),
            "overlap_score": round(overlap_score, 3)
        },
        verdict=Verdict(
            label=verdict_label,
            confidence=confidence,
            explanation=f"Evaluated as {verdict_label} with minimality '{min_label}'.",
            failure_taxonomy=sorted(taxonomy)
        )
    )
    return score
