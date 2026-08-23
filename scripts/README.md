# Reference build scripts

`build_static_reference.py` and `build_variable_reference.py` are the audited scripts used for release 1.000. They use repository-relative output paths and accept these optional environment variables for source/workspace locations:

- `HANLINK_BUILD_WORKSPACE`
- `HANLINK_UPSTREAM_DIR`
- `HANLINK_BRIDGE_DIR`
- `HANLINK_STATIC_BUILD_DIR` / `HANLINK_VF_BUILD_DIR`

The upstream files and archive hashes used for the published binaries are recorded in `SOURCES.md`.

`audit_release.py` and `check_dash_matrix.py` perform structural regression checks for language-sensitive `ccmp` behavior, vertical metrics, dash orientation, and the variable weight axis.
