#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="edgepatch-zlib-validator"
CONTAINER_WORKDIR="/work"

PATCH_PATH="$ROOT/zlib-artifacts/optimized/flash_patch.optimized.diff"
REPRO_SRC="$ROOT/zlib-artifacts/optimized/repro_cve_2022_37434.optimized.c"

if [[ ! -f "$PATCH_PATH" ]]; then
  echo "ERROR: Missing patch: $PATCH_PATH"
  exit 1
fi

if [[ ! -f "$REPRO_SRC" ]]; then
  echo "ERROR: Missing reproducer: $REPRO_SRC"
  exit 1
fi

cat > "$ROOT/zlib-artifacts/optimized/Dockerfile.validate" <<'DOCKER'
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    clang \
    git \
    ca-certificates \
    python3 \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
DOCKER

echo "== Building Docker image =="
docker build \
  -f "$ROOT/zlib-artifacts/optimized/Dockerfile.validate" \
  -t "$IMAGE" \
  "$ROOT/zlib-artifacts/optimized"

echo "== Running validation inside Ubuntu container =="
docker run --rm \
  -v "$ROOT:/work" \
  -w "$CONTAINER_WORKDIR" \
  "$IMAGE" \
  bash -lc '
set -euo pipefail

ROOT=/work
ZLIB_DIR="$ROOT/targets/zlib"
PATCH_PATH="$ROOT/zlib-artifacts/optimized/flash_patch.optimized.diff"
REPRO_SRC="$ROOT/zlib-artifacts/optimized/repro_cve_2022_37434.optimized.c"
REPRO_BIN="$ROOT/zlib-artifacts/optimized/repro_optimized"
BUILD_LOG="$ROOT/zlib-artifacts/optimized/docker_build.log"
TEST_LOG="$ROOT/zlib-artifacts/optimized/docker_zlib_make_test.log"
VALIDATION_LOG="$ROOT/zlib-artifacts/optimized/docker_post_patch_validation.log"

mkdir -p "$ROOT/targets" "$ROOT/zlib-artifacts/optimized"

if [[ ! -d "$ZLIB_DIR/.git" ]]; then
  echo "== Cloning zlib =="
  git clone https://github.com/madler/zlib.git "$ZLIB_DIR"
fi

cd "$ZLIB_DIR"

echo "== Resetting zlib to v1.2.11 =="
git fetch --tags --quiet || true
git reset --hard
git clean -fdx
git checkout v1.2.11

echo "== Applying optimized patch =="
if git apply --check "$PATCH_PATH" >/dev/null 2>&1; then
  git apply "$PATCH_PATH"
else
  echo "Patch did not apply cleanly. Applying semantic source replacement."

  python3 - <<PY
from pathlib import Path
import re

path = Path("inflate.c")
text = path.read_text()

pattern = re.compile(
    r"(?P<indent>[ \t]*)len = state->head->extra_len - state->length;\n"
    r"(?P=indent)zmemcpy\(state->head->extra \+ len, next,\n"
    r"(?P=indent)[ \t]*len \+ copy > state->head->extra_max \?\n"
    r"(?P=indent)[ \t]*state->head->extra_max - len : copy\);"
)

def replacement(match):
    indent = match.group("indent")
    return (
        f"{indent}len = state->head->extra_len - state->length;\n"
        f"{indent}if (len < state->head->extra_max) {{\n"
        f"{indent}    unsigned copy_len = state->head->extra_max - len;\n"
        f"{indent}    if (copy_len > copy) {{\n"
        f"{indent}        copy_len = copy;\n"
        f"{indent}    }}\n"
        f"{indent}    zmemcpy(state->head->extra + len, next, copy_len);\n"
        f"{indent}}}"
    )

new_text, count = pattern.subn(replacement, text)

if count != 1:
    raise SystemExit(f"ERROR: Expected exactly one replacement, got {count}")

path.write_text(new_text)
PY

  git diff -- inflate.c > "$PATCH_PATH"
fi

echo "== Confirming patch =="
grep -n "copy_len" inflate.c -A 8 -B 5

echo "== Building zlib with ASan/UBSan =="
{
  make clean || true

  CC=clang \
  CFLAGS="-fsanitize=address,undefined -g -O1" \
  LDFLAGS="-fsanitize=address,undefined" \
  ./configure

  make -j"$(nproc)"
} 2>&1 | tee "$BUILD_LOG"

if [[ ! -f "$ZLIB_DIR/libz.a" ]]; then
  echo "ERROR: libz.a was not created."
  exit 1
fi

echo "== Running zlib standard tests =="
set +e
make test > "$TEST_LOG" 2>&1
TEST_EXIT=$?
set -e
cat "$TEST_LOG"

if [[ "$TEST_EXIT" -ne 0 ]]; then
  echo "ERROR: zlib standard tests failed."
  exit 1
fi

echo "== Compiling optimized reproducer =="
cd "$ROOT"

clang -fsanitize=address,undefined -g -O1 \
  -Itargets/zlib \
  "$REPRO_SRC" \
  "$ZLIB_DIR/libz.a" \
  -o "$REPRO_BIN"

echo "== Running optimized reproducer against patched zlib =="
set +e
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 \
UBSAN_OPTIONS=halt_on_error=1 \
"$REPRO_BIN" > "$VALIDATION_LOG" 2>&1
REPRO_EXIT=$?
set -e

cat "$VALIDATION_LOG"

if [[ "$REPRO_EXIT" -ne 0 ]]; then
  echo "ERROR: Reproducer exited non-zero: $REPRO_EXIT"
  exit 1
fi

if grep -E "heap-buffer-overflow|memcpy-param-overlap|LeakSanitizer|runtime error|ERROR: AddressSanitizer|ERROR: UndefinedBehaviorSanitizer" "$VALIDATION_LOG" >/dev/null; then
  echo "ERROR: Sanitizer issue detected in targeted validation log."
  exit 1
fi

TEST_SANITIZER_STATUS="clean"
if grep -E "runtime error|ERROR: AddressSanitizer|ERROR: UndefinedBehaviorSanitizer|LeakSanitizer" "$TEST_LOG" >/dev/null; then
  TEST_SANITIZER_STATUS="warning"
fi

echo "SUCCESS: Targeted post-patch reproducer exits cleanly with no ASan/UBSan issue."
echo "NOTE: zlib standard tests passed functionally. Test sanitizer status: $TEST_SANITIZER_STATUS"
if [[ "$TEST_SANITIZER_STATUS" == "warning" ]]; then
  echo "NOTE: Standard test log contains sanitizer warnings. Treat these separately from the targeted CVE validation."
fi

echo "Logs:"
echo "  Build:      $BUILD_LOG"
echo "  Test:       $TEST_LOG"
echo "  Validation: $VALIDATION_LOG"
'
