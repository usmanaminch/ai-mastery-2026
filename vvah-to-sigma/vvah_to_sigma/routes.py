"""Derive URL routes for findings from source code, so web rules can be scoped
to the endpoint that actually reaches the vulnerable line.

Supported today:
  * Django   - follows ROOT_URLCONF and include() through urls.py files
  * Flask    - @app.route / @bp.route decorators
  * Templates - a finding in an HTML template is mapped to the view that renders it

Anything it cannot resolve is left unscoped (the rule watches all endpoints) and
the coverage report says so. It never guesses a route.
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path

RouteMap = dict[tuple[str, str], set[str]]


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, ValueError):
        return None


def _module_file(repo: Path, dotted: str) -> Path | None:
    base = repo.joinpath(*dotted.split("."))
    for cand in (base.with_suffix(".py"), base / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def _norm(route: str) -> str:
    return "/" + route.lstrip("/")


def _import_aliases(tree: ast.Module, here: Path, repo: Path) -> dict:
    """name -> (module file relative to repo, function name or None if it is a module).
    The special key "*" lists modules pulled in with `from x import *`."""
    aliases: dict = {}
    pkg_dir = here.parent
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            base_dir = pkg_dir
            for _ in range(node.level - 1):
                base_dir = base_dir.parent
            base = base_dir.joinpath(*(node.module or "").split(".")) if node.module else base_dir
        else:
            base = repo.joinpath(*(node.module or "").split("."))
        for a in node.names:
            if a.name == "*":
                for mod in (base.with_suffix(".py"), base / "__init__.py"):
                    if mod.is_file():
                        aliases.setdefault("*", []).append(str(mod.relative_to(repo)))
                        break
                continue
            name = a.asname or a.name
            sub = base / f"{a.name}.py"
            if sub.is_file():
                aliases[name] = (str(sub.relative_to(repo)), None)
                continue
            for mod in (base.with_suffix(".py"), base / "__init__.py"):
                if mod.is_file():
                    aliases[name] = (str(mod.relative_to(repo)), a.name)
                    break
    return aliases


def _str_arg(call: ast.Call, i: int = 0) -> str | None:
    if len(call.args) > i and isinstance(call.args[i], ast.Constant) and isinstance(call.args[i].value, str):
        return call.args[i].value
    return None


def _walk_urlconf(repo: Path, urls_file: Path, prefix: str, out: RouteMap, seen: set[Path]) -> None:
    if urls_file in seen:
        return
    seen.add(urls_file)
    tree = _parse(urls_file)
    if not tree:
        return
    aliases = _import_aliases(tree, urls_file, repo)
    for call in (n for n in ast.walk(tree) if isinstance(n, ast.Call)):
        fname = getattr(call.func, "id", None) or getattr(call.func, "attr", None)
        if fname not in ("path", "re_path", "url") or len(call.args) < 2:
            continue
        route = _str_arg(call)
        if route is None:
            continue
        if fname != "path":
            route = route.lstrip("^").rstrip("$")
        target = call.args[1]
        full = prefix + route
        if isinstance(target, ast.Call) and getattr(target.func, "id", None) == "include":
            inc = _str_arg(target)
            inc_file = _module_file(repo, inc) if inc else None
            if inc_file:
                _walk_urlconf(repo, inc_file, full, out, seen)
            continue
        if isinstance(target, ast.Call) and getattr(target.func, "attr", None) == "as_view":
            target = target.func.value
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            mod = aliases.get(target.value.id)
            if mod and mod[1] is None:
                out[(mod[0], target.attr)].add(_norm(full))
        elif isinstance(target, ast.Name):
            mod = aliases.get(target.id)
            if mod and mod[1]:
                out[(mod[0], mod[1])].add(_norm(full))
            else:
                for star in aliases.get("*", []):
                    star_tree = _parse(repo / star)
                    names = {n.name for n in (star_tree.body if star_tree else [])
                             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
                    if target.id in names:
                        out[(star, target.id)].add(_norm(full))
                        break


def _django_roots(repo: Path) -> list[Path]:
    roots = []
    for settings in repo.rglob("settings.py"):
        m = re.search(r"ROOT_URLCONF\s*=\s*['\"]([\w.]+)['\"]", settings.read_text(errors="replace"))
        if m:
            f = _module_file(repo, m.group(1))
            if f:
                roots.append(f)
    return roots


def _flask_routes(repo: Path, out: RouteMap) -> None:
    for py in repo.rglob("*.py"):
        if any(p in py.parts for p in (".venv", "venv", "node_modules", "site-packages")):
            continue
        tree = _parse(py)
        if not tree:
            continue
        for fn in (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
            for dec in fn.decorator_list:
                if isinstance(dec, ast.Call) and getattr(dec.func, "attr", None) in ("route", "get", "post"):
                    r = _str_arg(dec)
                    if r:
                        out[(str(py.relative_to(repo)), fn.name)].add(_norm(r))


def build_route_map(repo: Path) -> RouteMap:
    out: RouteMap = defaultdict(set)
    seen: set[Path] = set()
    for root in _django_roots(repo):
        _walk_urlconf(repo, root, "", out, seen)
    _flask_routes(repo, out)
    return out


def enclosing_function(repo: Path, rel_file: str, line: int) -> str | None:
    """Innermost def (or the class, for methods of a class-based view) containing `line`."""
    tree = _parse(repo / rel_file)
    if not tree:
        return None
    best, best_span = None, None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end = getattr(node, "end_lineno", node.lineno)
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            if start <= line <= end and (best_span is None or end - start < best_span):
                best, best_span = node, end - start
    if best is None:
        return None
    if isinstance(best, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef) and best in parent.body:
                return parent.name
    return best.name


def _template_renderers(repo: Path, rel_template: str) -> list[tuple[str, str]]:
    """Views that render a template, found by searching for its template-relative name."""
    parts = Path(rel_template).parts
    if "templates" not in parts:
        return []
    tname = "/".join(parts[parts.index("templates") + 1:])
    hits = []
    for py in repo.rglob("*.py"):
        if any(p in py.parts for p in (".venv", "venv", "node_modules", "site-packages")):
            continue
        text = py.read_text(errors="replace")
        if tname not in text:
            continue
        for i, ln in enumerate(text.splitlines(), 1):
            if tname in ln:
                fn = enclosing_function(repo, str(py.relative_to(repo)), i)
                if fn:
                    hits.append((str(py.relative_to(repo)), fn))
    return hits


def routes_for(repo: Path, route_map: RouteMap, rel_file: str, line: int) -> tuple[list[str], str]:
    """Return (routes, how) for a finding location. Empty list means unresolved."""
    if rel_file.endswith(".html"):
        found = sorted({r for key in _template_renderers(repo, rel_file) for r in route_map.get(key, ())})
        return found, "template->view" if found else "template not linked to a routed view"
    if not rel_file.endswith(".py") or not (repo / rel_file).is_file():
        return [], "not application code"
    fn = enclosing_function(repo, rel_file, line)
    if not fn:
        return [], "line is not inside a function"
    found = sorted(route_map.get((rel_file, fn), ()))
    return found, f"view {fn}" if found else f"function {fn} is not directly routed"


_CHANNELS = {
    # Django
    "GET": "query", "POST": "body", "body": "body", "FILES": "body", "data": "body",
    "META": "headers", "headers": "headers", "COOKIES": "cookies",
    # Flask
    "args": "query", "form": "body", "json": "body", "files": "body", "get_json": "body",
    "values": "query", "cookies": "cookies",
}


def _function_node(repo: Path, rel_file: str, name: str):
    tree = _parse(repo / rel_file)
    if not tree:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name:
            return node
    return None


def input_channels(repo: Path, rel_file: str, line: int) -> set[str]:
    """Where the enclosing view reads user input from: query, body, headers, cookies.
    Empty set means unknown (not a view, or no request access found)."""
    if rel_file.endswith(".html"):
        found: set[str] = set()
        for py, fn in _template_renderers(repo, rel_file):
            node = _function_node(repo, py, fn)
            if node:
                found |= _channels_in(node)
        return found
    if not rel_file.endswith(".py") or not (repo / rel_file).is_file():
        return set()
    fn = enclosing_function(repo, rel_file, line)
    node = _function_node(repo, rel_file, fn) if fn else None
    return _channels_in(node) if node else set()


def _channels_in(node) -> set[str]:
    found = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "request":
            ch = _CHANNELS.get(n.attr)
            if ch:
                found.add(ch)
    return found
