"""
Deterministic Source Map for EdgePatch Evaluation.
Maps changed line numbers to C-like functions without full AST parsing.
Limitations:
- simple, well-formed C-like functions only
- no K&R style support
- no macro-generated function bodies
- no full C preprocessor expansion
- no Tree-sitter in this first version
"""
import re
from pathlib import Path
from typing import List, Optional
from .models import FunctionRange

def extract_functions(source: str) -> List[FunctionRange]:
    functions: List[FunctionRange] = []
    brace_depth = 0
    line_num = 1
    idx = 0
    length = len(source)

    in_string = False
    in_char = False
    in_comment_line = False
    in_comment_block = False

    current_func_name: Optional[str] = None
    current_func_start_line: Optional[int] = None

    while idx < length:
        c = source[idx]
        nc = source[idx+1] if idx+1 < length else ''

        if c == '\n':
            line_num += 1
            if in_comment_line:
                in_comment_line = False
            idx += 1
            continue

        if in_comment_line:
            idx += 1
            continue
        if in_comment_block:
            if c == '*' and nc == '/':
                in_comment_block = False
                idx += 2
            else:
                idx += 1
            continue
        if in_string:
            if c == '\\':
                idx += 2
            elif c == '"':
                in_string = False
                idx += 1
            else:
                idx += 1
            continue
        if in_char:
            if c == '\\':
                idx += 2
            elif c == "'":
                in_char = False
                idx += 1
            else:
                idx += 1
            continue

        if c == '/' and nc == '/':
            in_comment_line = True
            idx += 2
            continue
        if c == '/' and nc == '*':
            in_comment_block = True
            idx += 2
            continue
        if c == '"':
            in_string = True
            idx += 1
            continue
        if c == "'":
            in_char = True
            idx += 1
            continue

        if c == '{':
            if brace_depth == 0:
                back_str = source[:idx].rstrip()
                last_paren_idx = back_str.rfind(')')
                last_brace_idx = max(back_str.rfind('{'), back_str.rfind('}'))
                
                if last_paren_idx > last_brace_idx:
                    paren_depth = 0
                    b_idx = last_paren_idx
                    while b_idx >= 0:
                        if back_str[b_idx] == ')': paren_depth += 1
                        elif back_str[b_idx] == '(': paren_depth -= 1
                        if paren_depth == 0:
                            break
                        b_idx -= 1
                    
                    if b_idx >= 0:
                        before_brace = back_str[last_paren_idx+1:].strip()
                        is_struct = bool(re.search(r'\b(struct|class|enum|union)\s+[a-zA-Z0-9_]+\s*$', before_brace) or \
                                         re.search(r'\b(struct|class|enum|union)\s*$', before_brace))
                        
                        if not is_struct and '=' not in before_brace:
                            pre_paren = back_str[:b_idx].strip()
                            m = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*$', pre_paren)
                            if m:
                                func_name = m.group(1)
                                if func_name not in ["if", "for", "while", "switch", "catch", "else", "do"]:
                                    current_func_name = func_name
                                    start_search_idx = pre_paren.rfind(';')
                                    start_search_idx2 = pre_paren.rfind('}')
                                    start_idx = max(start_search_idx, start_search_idx2)
                                    if start_idx == -1: 
                                        start_idx = 0
                                    else: 
                                        start_idx += 1
                                    
                                    start_line_calc = source[:start_idx].count('\n') + 1
                                    while start_idx < len(source) and source[start_idx].isspace():
                                        if source[start_idx] == '\n':
                                            start_line_calc += 1
                                        start_idx += 1
                                    
                                    current_func_start_line = start_line_calc

            brace_depth += 1
            idx += 1
            continue

        if c == '}':
            brace_depth -= 1
            if brace_depth == 0 and current_func_name is not None and current_func_start_line is not None:
                functions.append(FunctionRange(
                    name=current_func_name,
                    start_line=current_func_start_line,
                    end_line=line_num
                ))
                current_func_name = None
                current_func_start_line = None
            elif brace_depth < 0:
                brace_depth = 0
            idx += 1
            continue

        idx += 1

    return functions

def map_changed_lines(source_code: str, changed_lines: List[int]) -> List[str]:
    funcs = extract_functions(source_code)
    touched = set()
    for line in changed_lines:
        for f in funcs:
            if f.start_line <= line <= f.end_line:
                touched.add(f.name)
    return sorted(list(touched))
