# Reference build scripts

`build_static_reference.py` and `build_variable_reference.py` are the exact audited scripts used to produce release 1.000 in the build environment. Their source paths point to the release build workspace; for a clean-room rebuild, place the upstream archives recorded in `SOURCES.md` under a local source workspace and adjust the path constants at the top of the scripts.

`audit_release.py` performs structural regression checks for language-sensitive `ccmp` behavior, vertical metrics, dash orientation, and the variable weight axis.
