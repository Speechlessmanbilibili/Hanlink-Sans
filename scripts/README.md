# Reference build scripts

`fetch_sources.py` downloads the pinned Google Fonts Noto Sans SC and Hanken Grotesk variable TTFs, verifies their hashes, and creates the nine static source instances.

`build_static_reference.py` and `build_variable_reference.py` are the audited release build scripts. Their default source cache is `sources/`, their default bridge checkout is the sibling `CJK-Punct-Bridge` repository, and they accept these optional environment variables:

- `HANLINK_BUILD_WORKSPACE`
- `HANLINK_UPSTREAM_DIR`
- `HANLINK_BRIDGE_DIR`
- `HANLINK_STATIC_BUILD_DIR` / `HANLINK_VF_BUILD_DIR`
- `HANLINK_TEST_FONT` (selects a static or variable release file for the HarfBuzz/RAQM regression)

The upstream files and archive hashes used for the published binaries are recorded in `SOURCES.md`.

`HANLINK_REUSE_STATIC=1` and `HANLINK_REUSE_VF_INPUTS=1` opt into build-cache reuse. Normal release builds deliberately rebuild to prevent stale binaries.

`language_systems.py` pins the OpenType language registry and source-policy constants. `font_metadata.py` is the canonical source for project authorship, copyright, source attribution, URLs, license fields, and the internal font revision. `audit_release.py` and `check_dash_matrix.py` check that metadata plus all explicit Western language systems, all 46 Hanken punctuation mappings, invariant Hanken digits, CJK regional aliases, language-sensitive `ccmp`, vertical metrics, dash orientation, and the variable weight axis.
