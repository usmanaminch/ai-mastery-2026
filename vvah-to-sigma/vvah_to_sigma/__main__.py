import argparse
import json
from pathlib import Path

from .convert import convert


def main() -> None:
    ap = argparse.ArgumentParser(prog="vvah_to_sigma",
                                 description="Turn VVAH SARIF findings into Sigma rules and a coverage report.")
    ap.add_argument("sarif", type=Path, help="VVAH *_report.sarif file")
    ap.add_argument("--out", type=Path, default=Path("out"), help="output directory")
    ap.add_argument("--routes", type=Path, help="YAML mapping 'file' or 'file:line' to a URL path")
    ap.add_argument("--repo", type=Path,
                    help="scanned source tree; derives endpoint routes automatically (Django, Flask)")
    ap.add_argument("--min-confidence", type=float, default=0.0,
                    help="skip rule generation for findings below this VVAH confidence")
    ap.add_argument("--author", default="vvah-to-sigma")
    args = ap.parse_args()
    summary = convert(args.sarif, args.out, args.routes, args.min_confidence, args.author, args.repo)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
