# Third-Party Notices for EdgePatch Benchmark Snapshots

EdgePatch includes small source snapshots from upstream open-source C libraries solely for deterministic benchmark reproduction.

These snapshots are used by the structural patch scorer to map candidate patches to files, functions, and line regions. They are not distributed as modified production libraries.

## zlib

- Snapshot file: `benchmark/source_snapshots/zlib/inflate.c`
- Upstream project: zlib
- Upstream site: https://zlib.net/
- License: zlib License
- Benchmark case: `zlib-cve-2022-37434`
- Notes: The snapshot preserves the upstream copyright header. The upstream file refers to the distribution and use notice in `zlib.h`.

## libpng

- Snapshot file: `benchmark/source_snapshots/libpng/pngrtran.c`
- Upstream project: libpng
- Upstream site: https://www.libpng.org/pub/png/libpng.html
- License: libpng license
- Benchmark case: `libpng-cve-2025-64505`
- Notes: The snapshot preserves the upstream copyright header. The upstream file refers to the disclaimer and license in `png.h`.

## Expat

- Snapshot file: `benchmark/source_snapshots/expat/expat/lib/xmlparse.c`
- Upstream project: Expat XML Parser
- Upstream site: https://libexpat.github.io/
- License: MIT/X Consortium-style Expat license
- Benchmark case: `expat-cve-2022-25315`
- Notes: The snapshot preserves the upstream copyright and MIT-style license text in the file header.

## libxml2

- Snapshot file: `benchmark/source_snapshots/libxml2/parser.c`
- Upstream project: libxml2
- Upstream site: https://gitlab.gnome.org/GNOME/libxml2
- License: MIT License
- Benchmark case: `libxml2-cve-2022-40303`
- Notes: The snapshot preserves the upstream file header. The upstream file refers to the project `Copyright` file for license status.

## Benchmark Scope

The bundled benchmark snapshots are included to make the following command reproducible from a clean clone without requiring Gemini, Docker, internet access, pip-installed dependencies, or upstream source checkouts:

    python3 -m edgepatch bench

The benchmark evaluates structural patch scoring only. Behavioral validation belongs to full-pipeline case studies.
