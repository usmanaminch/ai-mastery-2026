from eval.patch_score.source_map import extract_functions, map_changed_lines

def test_extract_simple_function():
    code = """
int main() {
    return 0;
}
"""
    funcs = extract_functions(code)
    assert len(funcs) == 1
    assert funcs[0].name == "main"
    assert funcs[0].start_line == 2
    assert funcs[0].end_line == 4

def test_extract_multiline_signature():
    code = """
void 
complex_function(int a,
                 int b) 
{
    int c = a + b;
}
"""
    funcs = extract_functions(code)
    assert len(funcs) == 1
    assert funcs[0].name == "complex_function"
    assert funcs[0].start_line == 2

def test_extract_knr_function():
    code = """
int ZEXPORT inflate(strm, flush)
z_streamp strm;
int flush;
{
    return 0;
}
"""
    funcs = extract_functions(code)
    assert len(funcs) == 1
    assert funcs[0].name == "inflate"
    assert funcs[0].start_line == 2
    assert funcs[0].end_line == 7

def test_map_changed_lines():
    code = """
void foo() {
    int a = 1;
}

void bar() {
    int b = 2;
}
"""
    mapped = map_changed_lines(code, [3, 7])
    assert mapped == ["bar", "foo"]
