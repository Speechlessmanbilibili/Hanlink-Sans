"""Post-merge OpenType compatibility fixes for Hanlink Sans.

Hanlink keeps Hanken Grotesk and Noto Sans SC duplicate glyphs as hidden
layout targets, but only one source owns each Unicode cmap entry.  This module
reconnects source lookups whose original input glyph is hidden, and rebuilds
language systems so Latin and CJK features remain reachable without enabling
the CJK repeated-em-dash rule for explicit Western-language text.
"""

from collections import defaultdict
from copy import deepcopy
from fontTools.otlLib.builder import (
    buildLookup,
    buildSingleSubstSubtable,
    buildLigatureSubstSubtable,
    buildSinglePos,
    buildPairPosGlyphs,
    buildMarkBasePosSubtable,
)
from fontTools.ttLib.tables import otTables
from language_systems import (
    CJK_LANGUAGE_TAGS,
    HANKEN_SHARED_PUNCTUATION,
    WESTERN_LANGUAGE_SYSTEMS,
    WESTERN_SCRIPT_TAGS,
)


# Noto features that are useful across the ownership boundary.  We deliberately
# do not restore Noto's Latin liga/ccmp/locl wholesale: Hanken should remain the
# Latin design.  CJK U+2014 repeated-dash ccmp is handled separately below.
_NOTO_SINGLE_TAGS = ("fwid", "hwid", "pwid", "ruby", "vert", "vrt2")
_NOTO_LIGATURE_TAGS = ("dlig",)
_ENG_STRUCTURAL_TAGS = {"fwid", "hwid", "pwid", "vert", "vrt2", "locl"}


def _script(table, tag):
    for sr in table.ScriptList.ScriptRecord:
        if sr.ScriptTag == tag:
            return sr.Script
    return None


def _langsys(table, script_tag, lang_tag=None):
    script = _script(table, script_tag)
    if script is None:
        return None
    if lang_tag is None:
        return script.DefaultLangSys
    wanted = lang_tag.ljust(4)[:4]
    for lr in script.LangSysRecord:
        if lr.LangSysTag == wanted:
            return lr.LangSys
    return None


def _features_by_tag(table, langsys):
    out = {}
    if langsys is None:
        return out
    for fi in langsys.FeatureIndex:
        fr = table.FeatureList.FeatureRecord[fi]
        out.setdefault(fr.FeatureTag, []).append(fi)
    return out


def _append_unique(dst, values):
    for value in values:
        if value not in dst:
            dst.append(value)


def _merge_feature_record_lookups(table, dst_idx, src_indices):
    dst = table.FeatureList.FeatureRecord[dst_idx].Feature
    for src_idx in src_indices:
        src = table.FeatureList.FeatureRecord[src_idx].Feature
        _append_unique(dst.LookupListIndex, src.LookupListIndex)
    dst.LookupCount = len(dst.LookupListIndex)


def _inherit_features(table, target, source, *, exclude=()):
    """Add source FeatureIndices to target without mutating shared records.

    ``fontTools.merge`` feature records are often shared by multiple LangSys
    objects.  Mutating a record to merge lookups can therefore leak a CJK
    lookup into ENG (or vice versa).  We only union the references here and
    later canonicalize the target LangSys into private one-record-per-tag
    features.
    """
    if target is None or source is None:
        return
    excluded = set(exclude)
    indices = list(target.FeatureIndex)
    for idx in source.FeatureIndex:
        if table.FeatureList.FeatureRecord[idx].FeatureTag in excluded:
            continue
        _append_unique(indices, [idx])
    indices.sort()
    target.FeatureIndex = indices
    target.FeatureCount = len(indices)


def _append_lookup(table, subtables, lookup_type=None):
    subtables = [st for st in subtables if st is not None]
    if not subtables:
        return None
    lookup = buildLookup(subtables, table="GSUB")
    table.LookupList.Lookup.append(lookup)
    table.LookupList.LookupCount = len(table.LookupList.Lookup)
    return len(table.LookupList.Lookup) - 1


def _append_single_lookup(table, mapping):
    if not mapping:
        return None
    return _append_lookup(table, [buildSingleSubstSubtable(mapping)])



def _shift_context_lookup_refs(obj, insert_idx, seen=None):
    """Shift GSUB/GPOS contextual lookup references after LookupList insertion."""
    if seen is None:
        seen = set()
    if isinstance(obj, (str, int, float, bytes, type(None))):
        return
    oid = id(obj)
    if oid in seen:
        return
    seen.add(oid)
    if hasattr(obj, "LookupListIndex") and obj.__class__.__name__ in (
        "SubstLookupRecord", "PosLookupRecord"
    ):
        if obj.LookupListIndex >= insert_idx:
            obj.LookupListIndex += 1
    if isinstance(obj, (list, tuple)):
        for item in obj:
            _shift_context_lookup_refs(item, insert_idx, seen)
    elif hasattr(obj, "__dict__"):
        for key, value in obj.__dict__.items():
            if not key.startswith("_"):
                _shift_context_lookup_refs(value, insert_idx, seen)


def _insert_lookup(table, subtables, insert_idx=0):
    """Insert a lookup and keep every existing lookup reference valid."""
    subtables = [st for st in subtables if st is not None]
    if not subtables:
        return None
    lookup = buildLookup(subtables, table="GSUB")
    # Feature lookup references.
    for fr in table.FeatureList.FeatureRecord:
        fr.Feature.LookupListIndex = [
            i + 1 if i >= insert_idx else i
            for i in fr.Feature.LookupListIndex
        ]
    # Contextual/chained rules reference global LookupList indices too.
    for existing in table.LookupList.Lookup:
        for st in existing.SubTable:
            _shift_context_lookup_refs(st, insert_idx)
    table.LookupList.Lookup.insert(insert_idx, lookup)
    table.LookupList.LookupCount = len(table.LookupList.Lookup)
    return insert_idx


def _insert_single_lookup(table, mapping, insert_idx=0):
    if not mapping:
        return None
    return _insert_lookup(table, [buildSingleSubstSubtable(mapping)], insert_idx)


def _all_langsystems(table):
    for sr in table.ScriptList.ScriptRecord:
        if sr.Script.DefaultLangSys is not None:
            yield sr.ScriptTag, None, sr.Script.DefaultLangSys
        for lr in sr.Script.LangSysRecord:
            yield sr.ScriptTag, lr.LangSysTag, lr.LangSys


def _increment_feature_indices(table, insert_idx):
    for _script_tag, _lang_tag, ls in _all_langsystems(table):
        ls.FeatureIndex = [i + 1 if i >= insert_idx else i for i in ls.FeatureIndex]
        if ls.ReqFeatureIndex != 0xFFFF and ls.ReqFeatureIndex >= insert_idx:
            ls.ReqFeatureIndex += 1


def _insert_feature_record(table, tag, lookup_indices, feature_params=None):
    """Insert a sorted FeatureRecord and return its index."""
    if not lookup_indices:
        return None
    records = table.FeatureList.FeatureRecord
    insert_idx = 0
    while insert_idx < len(records) and records[insert_idx].FeatureTag <= tag:
        insert_idx += 1
    _increment_feature_indices(table, insert_idx)
    fr = otTables.FeatureRecord()
    fr.FeatureTag = tag
    feat = otTables.Feature()
    feat.FeatureParams = deepcopy(feature_params)
    feat.LookupListIndex = list(lookup_indices)
    feat.LookupCount = len(feat.LookupListIndex)
    fr.Feature = feat
    records.insert(insert_idx, fr)
    table.FeatureList.FeatureCount = len(records)
    return insert_idx


def _canonicalize_langsys_features(table, langsys):
    """Give one LangSys a private, single FeatureRecord for each active tag.

    Some merged fonts contain multiple active FeatureRecords with the same tag.
    Shapers are not required to combine those records, so a newly-added ``kern``
    can shadow Hanken kerning, or one ``liga`` can hide another.  For every
    duplicate tag we create a new private record containing the union of lookup
    indices in the original order, then point only this LangSys at that record.
    Shared source records are never mutated.
    """
    if langsys is None:
        return
    while True:
        groups = defaultdict(list)
        for idx in langsys.FeatureIndex:
            groups[table.FeatureList.FeatureRecord[idx].FeatureTag].append(idx)
        duplicate = next(((tag, inds) for tag, inds in groups.items() if len(inds) > 1), None)
        if duplicate is None:
            break
        tag, indices = duplicate
        lookups = []
        params = None
        for idx in indices:
            feat = table.FeatureList.FeatureRecord[idx].Feature
            if params is None and feat.FeatureParams is not None:
                params = feat.FeatureParams
            _append_unique(lookups, feat.LookupListIndex)
        new_idx = _insert_feature_record(table, tag, lookups, params)
        # Insertion shifts all existing FeatureIndices.  Recompute the active
        # duplicates by tag, then replace them with the private new record.
        old = [
            idx for idx in langsys.FeatureIndex
            if table.FeatureList.FeatureRecord[idx].FeatureTag == tag
        ]
        langsys.FeatureIndex = [idx for idx in langsys.FeatureIndex if idx not in old]
        langsys.FeatureIndex.append(new_idx)
        langsys.FeatureIndex.sort()
        langsys.FeatureCount = len(langsys.FeatureIndex)


def _canonicalize_all_langsystems(table):
    for _script_tag, _lang_tag, langsys in list(_all_langsystems(table)):
        _canonicalize_langsys_features(table, langsys)


def _sort_feature_records(table):
    """Sort FeatureRecords by tag and remap every stored feature index."""
    records = list(table.FeatureList.FeatureRecord)
    order = sorted(range(len(records)), key=lambda idx: (records[idx].FeatureTag, idx))
    if order == list(range(len(records))):
        return
    remap = {old: new for new, old in enumerate(order)}
    table.FeatureList.FeatureRecord = [records[idx] for idx in order]
    table.FeatureList.FeatureCount = len(records)
    for _script_tag, _lang_tag, langsys in _all_langsystems(table):
        langsys.FeatureIndex = sorted(remap[idx] for idx in langsys.FeatureIndex)
        langsys.FeatureCount = len(langsys.FeatureIndex)
        if langsys.ReqFeatureIndex != 0xFFFF:
            langsys.ReqFeatureIndex = remap[langsys.ReqFeatureIndex]
    variations = getattr(table, "FeatureVariations", None)
    if variations is not None:
        for record in variations.FeatureVariationRecord:
            substitution = record.FeatureTableSubstitution
            for subst_record in substitution.SubstitutionRecord:
                subst_record.FeatureIndex = remap[subst_record.FeatureIndex]


def _attach_feature_where_exposed(table, feature_idx, tag, *, include_eng):
    """Expose a supplemental feature only where that tag already existed."""
    if feature_idx is None:
        return
    # Feature insertion has already shifted all LangSys indices, so inspect the
    # current state.  Avoid using the new record itself to decide exposure.
    for _script_tag, lang_tag, ls in _all_langsystems(table):
        if not include_eng and lang_tag == "ENG ":
            continue
        existing = [
            i for i in ls.FeatureIndex
            if i != feature_idx and table.FeatureList.FeatureRecord[i].FeatureTag == tag
        ]
        if existing and feature_idx not in ls.FeatureIndex:
            ls.FeatureIndex.append(feature_idx)
            ls.FeatureIndex.sort()
            ls.FeatureCount = len(ls.FeatureIndex)


def _source_feature_indices(table, script_tag, lang_tag, feature_tag):
    ls = _langsys(table, script_tag, lang_tag)
    if ls is None:
        return []
    return [
        i for i in ls.FeatureIndex
        if table.FeatureList.FeatureRecord[i].FeatureTag == feature_tag
    ]


def _iter_lookup_subtables(table, feature_indices):
    for fi in feature_indices:
        fr = table.FeatureList.FeatureRecord[fi]
        for li in fr.Feature.LookupListIndex:
            lookup = table.LookupList.Lookup[li]
            for st in lookup.SubTable:
                typ = lookup.LookupType
                if typ == 7:
                    typ = st.ExtensionLookupType
                    st = st.ExtSubTable
                yield typ, st


def _restore_noto_cross_source_features(font, noto_source, noto_glyph_map, hanken_owned_cps):
    """Reconnect selected Noto features to Hanlink's public Hanken glyphs.

    Noto layout data is retained with hidden duplicate glyphs.  If Unicode A is
    publicly Hanken, however, Noto's original ``A -> fullwidth A`` lookup still
    starts from hidden Noto A.  We synthesize only the missing ownership-crossing
    rules while retaining the original Noto output glyphs/forms.
    """
    if noto_source is None or noto_glyph_map is None or "GSUB" not in noto_source:
        return
    final_gsub = font["GSUB"].table
    source_gsub = noto_source["GSUB"].table
    final_cmap = font.getBestCmap()
    source_cmap = noto_source.getBestCmap()
    reverse = defaultdict(list)
    for cp, gn in source_cmap.items():
        reverse[gn].append(cp)
    hanken_owned_cps = set(hanken_owned_cps or ())

    def encoded_cps(source_glyph):
        return reverse.get(source_glyph, ())

    def source_to_final(source_glyph, *, for_input=False):
        # Prefer the current public owner for encoded glyphs.  For input glyphs
        # this is exactly what reconnects hidden Noto data to Hanken.  For
        # outputs it also ensures hwid returns the public Hanken ASCII glyph.
        for cp in encoded_cps(source_glyph):
            if cp in final_cmap:
                return final_cmap[cp]
        return noto_glyph_map.get(source_glyph)

    def crosses_hanken(source_glyph):
        return any(cp in hanken_owned_cps for cp in encoded_cps(source_glyph))

    # Single substitutions: width forms, ruby and vertical alternates.
    for tag in _NOTO_SINGLE_TAGS:
        feature_indices = _source_feature_indices(source_gsub, "hani", "ZHS ", tag)
        mapping = {}
        for typ, st in _iter_lookup_subtables(source_gsub, feature_indices):
            if typ != 1 or not hasattr(st, "mapping"):
                continue
            for src, dst in st.mapping.items():
                if not crosses_hanken(src):
                    continue
                src_final = source_to_final(src, for_input=True)
                dst_final = source_to_final(dst)
                if src_final and dst_final and src_final != dst_final:
                    mapping[src_final] = dst_final
        li = _append_single_lookup(final_gsub, mapping)
        if li is not None:
            fi = _insert_feature_record(final_gsub, tag, [li])
            _attach_feature_where_exposed(final_gsub, fi, tag, include_eng=(tag in _ENG_STRUCTURAL_TAGS))

    # Noto discretionary ligatures are useful in CJK text (e.g. !! -> ‼ and
    # numbered CJK compatibility forms) but must not replace Hanken dlig in ENG.
    for tag in _NOTO_LIGATURE_TAGS:
        feature_indices = _source_feature_indices(source_gsub, "hani", "ZHS ", tag)
        mapping = {}
        for typ, st in _iter_lookup_subtables(source_gsub, feature_indices):
            if typ != 4 or not hasattr(st, "ligatures"):
                continue
            for first, ligatures in st.ligatures.items():
                for lig in ligatures:
                    seq = (first,) + tuple(lig.Component)
                    if not any(crosses_hanken(g) for g in seq):
                        continue
                    seq_final = tuple(source_to_final(g, for_input=True) for g in seq)
                    dst_final = source_to_final(lig.LigGlyph)
                    if None not in seq_final and dst_final:
                        mapping[seq_final] = dst_final
        if mapping:
            li = _append_lookup(final_gsub, [buildLigatureSubstSubtable(mapping)])
            fi = _insert_feature_record(final_gsub, tag, [li])
            _attach_feature_where_exposed(final_gsub, fi, tag, include_eng=False)

    # Preserve Noto's CJK repeated HORIZONTAL BAR behavior (U+2015) without
    # importing Noto's Latin composition ccmp into Hanken text.  U+2014 is
    # deliberately left to CJK Punct Bridge.
    ccmp_indices = _source_feature_indices(source_gsub, "hani", "ZHS ", "ccmp")
    ccmp_mapping = {}
    for typ, st in _iter_lookup_subtables(source_gsub, ccmp_indices):
        if typ != 4 or not hasattr(st, "ligatures"):
            continue
        for first, ligatures in st.ligatures.items():
            for lig in ligatures:
                seq = (first,) + tuple(lig.Component)
                seq_cps = []
                ok = True
                for g in seq:
                    cps = encoded_cps(g)
                    if not cps:
                        ok = False
                        break
                    seq_cps.append(cps[0])
                if not ok or not seq_cps or any(cp != 0x2015 for cp in seq_cps):
                    continue
                seq_final = tuple(source_to_final(g, for_input=True) for g in seq)
                dst_final = source_to_final(lig.LigGlyph)
                if None not in seq_final and dst_final:
                    ccmp_mapping[seq_final] = dst_final
    if ccmp_mapping:
        li = _append_lookup(final_gsub, [buildLigatureSubstSubtable(ccmp_mapping)])
        fi = _insert_feature_record(final_gsub, "ccmp", [li])
        _attach_feature_where_exposed(final_gsub, fi, "ccmp", include_eng=False)



def _append_gpos_lookup(table, subtables):
    subtables = [st for st in subtables if st is not None]
    if not subtables:
        return None
    lookup = buildLookup(subtables, table="GPOS")
    table.LookupList.Lookup.append(lookup)
    table.LookupList.LookupCount = len(table.LookupList.Lookup)
    return len(table.LookupList.Lookup) - 1


def _single_pos_records(st):
    """Yield ``(glyph, ValueRecord)`` from a GPOS SinglePos subtable."""
    if getattr(st, "Format", None) == 1:
        for glyph in st.Coverage.glyphs:
            yield glyph, st.Value
    elif getattr(st, "Format", None) == 2:
        for glyph, value in zip(st.Coverage.glyphs, st.Value):
            yield glyph, value


def _pair_pos_records(st, source_glyphs):
    """Yield explicit pair adjustments from PairPos format 1/2.

    Class kerning is expanded only over source glyphs that are encoded or
    explicitly present in ClassDef2.  This keeps the supplemental cross-source
    lookup compact while covering every glyph that can be reached from normal
    Unicode text or an explicit class assignment.
    """
    if getattr(st, "Format", None) == 1:
        for first, pairset in zip(st.Coverage.glyphs, st.PairSet):
            for rec in pairset.PairValueRecord:
                yield first, rec.SecondGlyph, rec.Value1, rec.Value2
        return
    if getattr(st, "Format", None) != 2:
        return

    class1 = defaultdict(list)
    for glyph in st.Coverage.glyphs:
        class1[st.ClassDef1.classDefs.get(glyph, 0)].append(glyph)
    class2 = defaultdict(list)
    candidates = set(source_glyphs) | set(st.ClassDef2.classDefs)
    for glyph in candidates:
        class2[st.ClassDef2.classDefs.get(glyph, 0)].append(glyph)

    for class1_id, row in enumerate(st.Class1Record):
        firsts = class1.get(class1_id, ())
        if not firsts:
            continue
        for class2_id, rec in enumerate(row.Class2Record):
            seconds = class2.get(class2_id, ())
            if not seconds:
                continue
            # Zero-valued records are semantically inert and can be skipped.
            values = (rec.Value1, rec.Value2)
            nonzero = False
            for value in values:
                if value is None:
                    continue
                for field in (
                    "XPlacement", "YPlacement", "XAdvance", "YAdvance",
                    "XPlaDevice", "YPlaDevice", "XAdvDevice", "YAdvDevice",
                ):
                    if getattr(value, field, None):
                        nonzero = True
                        break
                if nonzero:
                    break
            if not nonzero:
                continue
            for first in firsts:
                for second in seconds:
                    yield first, second, rec.Value1, rec.Value2


def _restore_noto_cross_source_positioning(
    font, noto_source, noto_glyph_map, hanken_owned_cps, bridge_owned_cps
):
    """Reconnect Noto GPOS rules that cross Hanlink's source boundaries.

    ``fontTools.merge`` correctly keeps each source lookup, but a lookup that
    originally referred to (for example) a Noto comma can no longer see that
    Unicode character when the public cmap entry is owned by the punctuation
    bridge.  The same applies to Noto CJK mark attachment when the combining
    mark is publicly owned by Hanken.

    We add only *cross-source* positioning rules:

    * Hanken-Hanken positioning stays Hanken's design.
    * Noto-Noto positioning remains in the original Noto lookup.
    * Bridge-Bridge positioning remains in the bridge lookup.
    * Hanken/Noto/Bridge mixed pairs and mark attachments are restored from
      Noto so CJK punctuation and vertical layout keep their source behavior.
    """
    if (
        noto_source is None
        or noto_glyph_map is None
        or "GPOS" not in font
        or "GPOS" not in noto_source
    ):
        return

    final = font["GPOS"].table
    source = noto_source["GPOS"].table
    final_cmap = font.getBestCmap()
    source_cmap = noto_source.getBestCmap()
    final_order = set(font.getGlyphOrder())
    source_encoded = set(source_cmap.values())
    reverse = defaultdict(list)
    for cp, glyph in source_cmap.items():
        reverse[glyph].append(cp)
    hanken_owned_cps = set(hanken_owned_cps or ())
    bridge_owned_cps = set(bridge_owned_cps or ())

    def hidden_name(source_glyph):
        return noto_glyph_map.get(source_glyph, source_glyph)

    def variants(source_glyph):
        """Return reachable final glyph variants as ``(glyph, owner)``."""
        hidden = hidden_name(source_glyph)
        out = []
        seen = set()
        cps = reverse.get(source_glyph, ())
        for cp in cps:
            target = final_cmap.get(cp)
            if target is None:
                continue
            if cp in bridge_owned_cps:
                owner = "B"
            elif cp in hanken_owned_cps:
                owner = "H"
            else:
                owner = "N"
            key = (target, owner)
            if key not in seen:
                seen.add(key)
                out.append(key)
        if out:
            return out
        # Unencoded layout glyphs may have both a bridge copy (original name)
        # and a renamed Noto copy.  Keep both reachable variants.
        if source_glyph in final_order and source_glyph != hidden:
            out.append((source_glyph, "B"))
        if hidden in final_order:
            out.append((hidden, "N"))
        return out

    def attach(tag, subtables):
        li = _append_gpos_lookup(final, subtables)
        if li is None:
            return
        fi = _insert_feature_record(final, tag, [li])
        _attach_feature_where_exposed(final, fi, tag, include_eng=True)

    # Do not transplant Noto single-position deltas (halt/palt/vhal/vpal)
    # onto Hanken-owned glyphs.  Those deltas assume Noto's own advance widths
    # (often 1000 units) and can produce invalid negative advances on Hanken
    # symbols.  Bridge/Noto-owned punctuation already retains the original
    # single-position lookups from its source font.

    # Pair positioning.  Expand Noto's class kerning into a compact explicit
    # lookup containing only pairs whose two public glyphs come from different
    # Hanlink sources.  Same-source pairs are intentionally left to the source
    # font that owns them, preventing double kerning.
    for tag in ("kern", "vkrn"):
        indices = _source_feature_indices(source, "hani", None, tag)
        pairs = {}
        for typ, st in _iter_lookup_subtables(source, indices):
            if typ != 2:
                continue
            for left, right, value1, value2 in _pair_pos_records(st, source_encoded):
                for left_final, left_owner in variants(left):
                    for right_final, right_owner in variants(right):
                        if left_owner == right_owner:
                            continue
                        key = (left_final, right_final)
                        # PairPos subtable order gives earlier explicit pairs
                        # precedence; preserve the first source value we see.
                        pairs.setdefault(
                            key, (deepcopy(value1), deepcopy(value2))
                        )
        if pairs:
            attach(tag, buildPairPosGlyphs(pairs, font.getReverseGlyphMap()))

    # Mark-to-base positioning.  Noto's CJK bases are retained, while common
    # combining marks are publicly Hanken glyphs.  Split by mark owner so the
    # supplemental lookup contains only cross-source attachments and cannot
    # double-apply to a same-source base.
    for tag in ("mark", "vert"):
        indices = _source_feature_indices(source, "hani", None, tag)
        subtables = []
        for typ, st in _iter_lookup_subtables(source, indices):
            if typ != 4:
                continue
            source_marks = {}
            for glyph, rec in zip(st.MarkCoverage.glyphs, st.MarkArray.MarkRecord):
                source_marks[glyph] = (rec.Class, rec.MarkAnchor)
            source_bases = {}
            for glyph, rec in zip(st.BaseCoverage.glyphs, st.BaseArray.BaseRecord):
                source_bases[glyph] = list(rec.BaseAnchor)

            # Owners represented by reachable mark glyphs in this subtable.
            owners = set()
            for glyph in source_marks:
                owners.update(owner for _target, owner in variants(glyph))
            for mark_owner in owners:
                marks = {}
                for glyph, (mark_class, anchor) in source_marks.items():
                    for target, owner in variants(glyph):
                        if owner == mark_owner:
                            marks[target] = (mark_class, deepcopy(anchor))
                if not marks:
                    continue
                bases = {}
                for glyph, anchors in source_bases.items():
                    for target, owner in variants(glyph):
                        if owner == mark_owner:
                            continue
                        bases[target] = {
                            class_id: deepcopy(anchor)
                            for class_id, anchor in enumerate(anchors)
                            if anchor is not None
                        }
                bases = {glyph: anchors for glyph, anchors in bases.items() if anchors}
                if marks and bases:
                    subtables.append(
                        buildMarkBasePosSubtable(
                            marks, bases, font.getReverseGlyphMap()
                        )
                    )
        if subtables:
            attach(tag, subtables)


def _clone_script_record(table, new_tag, source_tag="hani"):
    """Clone a source ScriptRecord when a Unicode script needs a dedicated path."""
    existing = _script(table, new_tag)
    if existing is not None:
        return existing
    source = _script(table, source_tag)
    if source is None:
        return None
    sr = otTables.ScriptRecord()
    sr.ScriptTag = new_tag
    sr.Script = deepcopy(source)
    table.ScriptList.ScriptRecord.append(sr)
    table.ScriptList.ScriptRecord.sort(key=lambda rec: rec.ScriptTag)
    table.ScriptList.ScriptCount = len(table.ScriptList.ScriptRecord)
    return sr.Script


def _ensure_langsys(script, tag, feature_indices):
    for lr in script.LangSysRecord:
        if lr.LangSysTag == tag:
            return lr.LangSys, False
    lr = otTables.LangSysRecord()
    lr.LangSysTag = tag
    ls = otTables.LangSys()
    ls.LookupOrder = None
    ls.ReqFeatureIndex = 0xFFFF
    ls.FeatureIndex = sorted(dict.fromkeys(feature_indices))
    ls.FeatureCount = len(ls.FeatureIndex)
    lr.LangSys = ls
    script.LangSysRecord.append(lr)
    script.LangSysRecord.sort(key=lambda rec: rec.LangSysTag)
    script.LangSysCount = len(script.LangSysRecord)
    return ls, True


def _private_langsys_feature(table, langsys, tag, prepend_lookup_indices):
    """Replace one active feature tag with a private lookup-union for a LangSys."""
    if langsys is None:
        return None
    old_indices = [
        idx for idx in langsys.FeatureIndex
        if table.FeatureList.FeatureRecord[idx].FeatureTag == tag
    ]
    lookups = list(prepend_lookup_indices)
    params = None
    for idx in old_indices:
        feat = table.FeatureList.FeatureRecord[idx].Feature
        if params is None and feat.FeatureParams is not None:
            params = feat.FeatureParams
        _append_unique(lookups, feat.LookupListIndex)
    if not lookups:
        return None
    new_idx = _insert_feature_record(table, tag, lookups, params)
    # Feature insertion shifts every existing FeatureIndex. Re-identify the old
    # records by tag and replace them with the new private record.
    langsys.FeatureIndex = [
        idx for idx in langsys.FeatureIndex
        if table.FeatureList.FeatureRecord[idx].FeatureTag != tag
    ]
    langsys.FeatureIndex.append(new_idx)
    langsys.FeatureIndex.sort()
    langsys.FeatureCount = len(langsys.FeatureIndex)
    return new_idx


def _install_western_punctuation_locl(font, hanken_hidden, hanken_common):
    """Use Hanken punctuation in explicit Western-language script runs.

    Default language systems and all explicit CJK language systems remain on
    the bridge/Noto path.  Existing Hanken language-specific locl behavior is
    preserved after the early Bridge -> hidden-Hanken remap.
    """
    if not hanken_hidden or "GSUB" not in font:
        return
    gsub = font["GSUB"].table
    cmap = font.getBestCmap()
    shared = set(HANKEN_SHARED_PUNCTUATION)
    if set(hanken_hidden) != shared:
        raise RuntimeError(
            "Bridge/Hanken punctuation overlap drifted: "
            f"expected {len(shared)}, got {len(hanken_hidden)}"
        )
    mapping = {
        cmap[cp]: hanken_hidden[cp]
        for cp in HANKEN_SHARED_PUNCTUATION
        if cp in cmap and cmap[cp] != hanken_hidden[cp]
    }
    li = _insert_single_lookup(gsub, mapping, 0)
    if li is None:
        return

    existing_targets = []
    new_targets = []
    base_features = list(hanken_common.values())
    for script_tag in WESTERN_SCRIPT_TAGS:
        script = _script(gsub, script_tag)
        if script is None:
            script = _clone_script_record(gsub, script_tag, "latn")
        for lang in WESTERN_LANGUAGE_SYSTEMS[script_tag]:
            langsys, created = _ensure_langsys(script, lang, base_features)
            if created:
                new_targets.append(langsys)
            else:
                _sanitize_western_langsys(
                    gsub, langsys, hanken_common, keep_current_locl=True
                )
                existing_targets.append(langsys)

    for langsys in existing_targets:
        _private_langsys_feature(gsub, langsys, "locl", [li])

    shared_feature = _insert_feature_record(gsub, "locl", [li])
    for langsys in new_targets:
        langsys.FeatureIndex = [
            idx for idx in langsys.FeatureIndex
            if gsub.FeatureList.FeatureRecord[idx].FeatureTag != "locl"
        ]
        langsys.FeatureIndex.append(shared_feature)
        langsys.FeatureIndex.sort()
        langsys.FeatureCount = len(langsys.FeatureIndex)


def _install_noto_nonlatin_shared_ccmp(
    font, noto_source, noto_glyph_map, hanken_owned_cps
):
    """Switch ambiguous Hanken-owned marks/symbols back to Noto by script.

    Hanken intentionally owns Latin text and common Western symbols.  A few of
    its encoded glyphs, however, are also genuine Greek characters (Delta,
    Omega, mu, pi, Greek punctuation) or combining marks used with Greek,
    Cyrillic and Bopomofo.  Leaving those public Hanken glyphs inside an
    otherwise Noto script causes visible style seams and can break Noto ccmp.

    The remap is an early private ccmp lookup, so Noto's original ccmp/locl and
    GPOS can consume their native hidden glyphs afterwards.  Latin runs are not
    affected.
    """
    if (
        noto_source is None
        or noto_glyph_map is None
        or "GSUB" not in font
        or "GSUB" not in noto_source
    ):
        return
    gsub = font["GSUB"].table
    final_cmap = font.getBestCmap()
    noto_cmap = noto_source.getBestCmap()
    hanken_owned = set(hanken_owned_cps or ())

    combining = {
        cp for cp in hanken_owned
        if 0x0300 <= cp <= 0x036F and cp in noto_cmap
    }
    greek = {
        cp for cp in hanken_owned
        if 0x0370 <= cp <= 0x03FF and cp in noto_cmap
    }
    # Bopomofo tone marks that overlap Hanken; spacing acute/grave are Noto-only.
    bopomofo_marks = {
        cp for cp in hanken_owned
        if cp in (0x02C7, 0x02D9) and cp in noto_cmap
    } | combining

    script_cps = {
        "grek": greek | combining,
        "cyrl": combining,
        "bopo": bopomofo_marks,
    }
    union = set().union(*script_cps.values())
    mapping = {}
    for cp in sorted(union):
        public = final_cmap.get(cp)
        src = noto_cmap.get(cp)
        hidden = noto_glyph_map.get(src) if src else None
        if public and hidden and public != hidden:
            mapping[public] = hidden
    li = _insert_single_lookup(gsub, mapping, 0)
    if li is None:
        return

    # Noto relies on DFLT/hani for Bopomofo. Give it an explicit script record
    # so the shared tone-mark remap and Noto layout data are selected together.
    _clone_script_record(gsub, "bopo", "hani")

    for script_tag, cps in script_cps.items():
        script = _script(gsub, script_tag)
        if script is None:
            continue
        # The shared lookup contains a superset, but script itemization keeps
        # unrelated characters in separate runs. Keeping one early lookup also
        # avoids repeated global LookupList insertions.
        systems = []
        if script.DefaultLangSys is not None:
            systems.append(script.DefaultLangSys)
        systems.extend(lr.LangSys for lr in script.LangSysRecord)
        for langsys in systems:
            _private_langsys_feature(gsub, langsys, "ccmp", [li])

    if "GPOS" in font:
        _clone_script_record(font["GPOS"].table, "bopo", "hani")


def _hanken_common_features(table, hanken_source):
    """Return one source-pure Hanken FeatureRecord per non-locl tag.

    The preserved Hanken language system can reference supplemental records
    inserted earlier by Hanlink.  The original Hanken record for a duplicated
    tag is the last record referenced by that system after fontTools.merge, so
    select only that record.  This prevents Noto dlig/ccmp from leaking into
    Western-script language systems.
    """
    by_tag = _features_by_tag(table, hanken_source)
    out = {}
    for tag, indices in by_tag.items():
        if tag == "locl" or not indices:
            continue
        out[tag] = indices[-1]
    return out


def _set_feature_indices(langsys, indices):
    if langsys is None:
        return
    langsys.FeatureIndex = sorted(dict.fromkeys(indices))
    langsys.FeatureCount = len(langsys.FeatureIndex)


def _sanitize_western_langsys(
    table,
    langsys,
    hanken_common,
    *,
    keep_current_locl=False,
    structural_tags=_ENG_STRUCTURAL_TAGS - {"locl"},
):
    """Make a Western-script LangSys Hanken-centric.

    Hanken supplies the alphabetic typography.  Hanlink keeps only structural
    Noto/bridge width/vertical features that are meaningful across ownership
    boundaries.  A language-specific Hanken ``locl`` can be retained when the
    source Hanken language system had one.
    """
    if langsys is None:
        return
    current = _features_by_tag(table, langsys)
    chosen = list(hanken_common.values())
    for tag in sorted(structural_tags):
        _append_unique(chosen, current.get(tag, []))
    if keep_current_locl:
        _append_unique(chosen, current.get("locl", []))
    _set_feature_indices(langsys, chosen)


def _object_mentions_glyphs(obj, glyph_names, seen=None):
    """Return source glyph names referenced anywhere in an OT subtable object."""
    if seen is None:
        seen = set()
    oid = id(obj)
    if oid in seen:
        return set()
    if isinstance(obj, str):
        return {obj} if obj in glyph_names else set()
    if isinstance(obj, (int, float, bytes, type(None))):
        return set()
    seen.add(oid)
    out = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            out.update(_object_mentions_glyphs(key, glyph_names, seen))
            out.update(_object_mentions_glyphs(value, glyph_names, seen))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            out.update(_object_mentions_glyphs(item, glyph_names, seen))
    elif hasattr(obj, "__dict__"):
        for key, value in obj.__dict__.items():
            if not key.startswith("_"):
                out.update(_object_mentions_glyphs(value, glyph_names, seen))
    return out


def _source_feature_overlap_cps(source_table, feature_indices, glyph_to_cp):
    wanted = set(glyph_to_cp)
    used = set()
    for fi in feature_indices:
        feature = source_table.FeatureList.FeatureRecord[fi].Feature
        for li in feature.LookupListIndex:
            lookup = source_table.LookupList.Lookup[li]
            for subtable in lookup.SubTable:
                used.update(_object_mentions_glyphs(subtable, wanted))
    return {glyph_to_cp[glyph] for glyph in used}



def _add_direct_bridge_mappings_to_hanken_feature(font, feature_idx, cps, hanken_hidden):
    """Extend a Hanken single-substitution feature across Bridge locl inputs."""
    if feature_idx is None or not cps:
        return
    table = font["GSUB"].table
    cmap = font.getBestCmap()
    feature = table.FeatureList.FeatureRecord[feature_idx].Feature
    mapping = {}
    locl_maps = []
    for record in table.FeatureList.FeatureRecord:
        if record.FeatureTag != "locl":
            continue
        for lookup_idx in record.Feature.LookupListIndex:
            lookup = table.LookupList.Lookup[lookup_idx]
            for subtable in lookup.SubTable:
                typ = lookup.LookupType
                if typ == 7:
                    typ = subtable.ExtensionLookupType
                    subtable = subtable.ExtSubTable
                if typ == 1 and hasattr(subtable, "mapping"):
                    locl_maps.append(subtable.mapping)
    # Existing Hanken feature lookups already know hidden-Hanken -> Hanken-alt.
    # Mirror those substitutions onto the public Bridge input and every locl
    # intermediate reachable before this feature runs.
    for cp in sorted(cps):
        public = cmap.get(cp)
        hidden = hanken_hidden.get(cp)
        if public is None or hidden is None or public == hidden:
            continue
        output = None
        for li in feature.LookupListIndex:
            lookup = table.LookupList.Lookup[li]
            for st in lookup.SubTable:
                typ = lookup.LookupType
                if typ == 7:
                    typ = st.ExtensionLookupType
                    st = st.ExtSubTable
                if typ == 1 and hasattr(st, "mapping") and hidden in st.mapping:
                    output = st.mapping[hidden]
                    break
            if output is not None:
                break
        if output is None:
            continue
        candidates = {public}
        changed = True
        while changed:
            changed = False
            for locl_map in locl_maps:
                for source in tuple(candidates):
                    target = locl_map.get(source)
                    if target is not None and target not in candidates:
                        candidates.add(target)
                        changed = True
        for source in candidates - {hidden}:
            mapping[source] = output
    li = _insert_single_lookup(table, mapping, 0)
    if li is not None:
        feature.LookupListIndex.append(li)
        feature.LookupListIndex.sort()
        feature.LookupCount = len(feature.LookupListIndex)


def _prepend_bridge_to_hanken_intermediate(font, feature_idx, cps, hanken_hidden):
    """Insert an early Bridge -> hidden-Hanken remap inside a contextual feature."""
    if feature_idx is None or not cps:
        return
    table = font["GSUB"].table
    cmap = font.getBestCmap()
    mapping = {
        cmap[cp]: hanken_hidden[cp]
        for cp in sorted(cps)
        if cp in cmap and cp in hanken_hidden and cmap[cp] != hanken_hidden[cp]
    }
    if not mapping:
        return
    # Insert globally before source lookups; then attach only to this feature.
    li = _insert_single_lookup(table, mapping, 0)
    feature = table.FeatureList.FeatureRecord[feature_idx].Feature
    if li not in feature.LookupListIndex:
        feature.LookupListIndex.append(li)
        feature.LookupListIndex.sort()
        feature.LookupCount = len(feature.LookupListIndex)


def _restore_hanken_bridge_gsub_inputs(font, hanken_source, hanken_hidden, hanken_common):
    """Reconnect Hanken GSUB rules whose input punctuation is Bridge-owned."""
    if not hanken_source or not hanken_hidden or "GSUB" not in hanken_source:
        return
    source = hanken_source["GSUB"].table
    source_cmap = hanken_source.getBestCmap()
    overlap = {source_cmap[cp]: cp for cp in hanken_hidden if cp in source_cmap}
    if not overlap:
        return

    # Common Hanken features such as aalt/ss03 can map directly from the public
    # Bridge glyph to the same Hanken alternate as the hidden source glyph.
    source_default = _langsys(source, "latn", None) or _langsys(source, "DFLT", None)
    source_by_tag = _features_by_tag(source, source_default)
    for tag, final_idx in hanken_common.items():
        cps = _source_feature_overlap_cps(source, source_by_tag.get(tag, ()), overlap)
        _add_direct_bridge_mappings_to_hanken_feature(
            font, final_idx, cps, hanken_hidden
        )

    # Contextual language-specific locl (currently Catalan l·l) needs the
    # hidden Hanken punctuation *before* its original context lookup executes.
    for script_tag in ("DFLT", "latn"):
        src_script = _script(source, script_tag)
        if src_script is None:
            continue
        for src_lr in src_script.LangSysRecord:
            src_locl = _features_by_tag(source, src_lr.LangSys).get("locl", ())
            cps = _source_feature_overlap_cps(source, src_locl, overlap)
            if not cps:
                continue
            dst_ls = _langsys(font["GSUB"].table, script_tag, src_lr.LangSysTag)
            if dst_ls is None:
                continue
            dst_locl = _features_by_tag(font["GSUB"].table, dst_ls).get("locl", ())
            for final_idx in dst_locl:
                _prepend_bridge_to_hanken_intermediate(
                    font, final_idx, cps, hanken_hidden
                )

def fix_hanlink_language_systems(
    font,
    hanken_hidden=None,
    hanken_source=None,
    noto_source=None,
    noto_glyph_map=None,
    hanken_owned_cps=None,
    bridge_owned_cps=None,
):
    """Repair merged OpenType behavior across Western and CJK scripts."""
    if "GSUB" in font:
        gsub = font["GSUB"].table

        _restore_noto_cross_source_features(
            font, noto_source, noto_glyph_map, hanken_owned_cps or ()
        )
        # Hanken-only provenance survives in language-specific Latin systems.
        provenance = _langsys(gsub, "latn", "TRK") or _langsys(gsub, "latn", "AZE")
        if provenance is None:
            raise RuntimeError("Cannot locate Hanken Latin feature provenance LangSys")
        hanken_common = _hanken_common_features(gsub, provenance)

        # DFLT is intentionally the mixed/CJK-oriented fallback. Preserve its
        # default and every explicit CJK regional path, while keeping Hanken's
        # alphabetic typography reachable inside those CJK language runs.
        dflt_default = _langsys(gsub, "DFLT", None)
        dflt_script = _script(gsub, "DFLT")
        if dflt_script is not None:
            for lr in dflt_script.LangSysRecord:
                if lr.LangSysTag in CJK_LANGUAGE_TAGS:
                    if lr.LangSysTag == "ZHS ":
                        _inherit_features(
                            gsub, lr.LangSys, dflt_default, exclude=("locl",)
                        )
                    _append_unique(lr.LangSys.FeatureIndex, hanken_common.values())
                    lr.LangSys.FeatureIndex.sort()
                    lr.LangSys.FeatureCount = len(lr.LangSys.FeatureIndex)

        # Latin letters are always Hanken, but the Latin script default keeps
        # bridge/Noto punctuation. Explicit Western languages are created and
        # switched to Hanken punctuation below. Explicit CJK languages retain
        # their corresponding bridge region plus Hanken alphabetic features.
        latn = _script(gsub, "latn")
        if latn is not None:
            _append_unique(latn.DefaultLangSys.FeatureIndex, hanken_common.values())
            latn.DefaultLangSys.FeatureIndex.sort()
            latn.DefaultLangSys.FeatureCount = len(latn.DefaultLangSys.FeatureIndex)
            for lr in latn.LangSysRecord:
                if lr.LangSysTag in CJK_LANGUAGE_TAGS:
                    _append_unique(lr.LangSys.FeatureIndex, hanken_common.values())
                    lr.LangSys.FeatureIndex.sort()
                    lr.LangSys.FeatureCount = len(lr.LangSys.FeatureIndex)
                else:
                    _sanitize_western_langsys(
                        gsub, lr.LangSys, hanken_common, keep_current_locl=True
                    )

        # Shared Western punctuation is Hanken only for explicit registered
        # languages in Western scripts. Script defaults and all CJK regions
        # remain bridge/Noto-oriented.
        _install_western_punctuation_locl(font, hanken_hidden, hanken_common)

        # Reconnect Hanken features only after the final Western locl path is
        # installed, so repairs include every intermediate glyph it can emit.
        _restore_hanken_bridge_gsub_inputs(
            font, hanken_source, hanken_hidden, hanken_common
        )

        # Restore Noto-native shared Greek/Cyrillic/Bopomofo marks before the
        # source ccmp/locl lookups execute.
        _install_noto_nonlatin_shared_ccmp(
            font, noto_source, noto_glyph_map, hanken_owned_cps or ()
        )

        # Canonicalize every active LangSys now that source policy is explicit.
        # This removes duplicate same-tag FeatureRecords that some shapers may
        # otherwise treat inconsistently.
        _canonicalize_all_langsystems(gsub)
        _sort_feature_records(gsub)

    _restore_noto_cross_source_positioning(
        font, noto_source, noto_glyph_map, hanken_owned_cps or (), bridge_owned_cps or ()
    )
    if "GPOS" in font:
        _canonicalize_all_langsystems(font["GPOS"].table)
        _sort_feature_records(font["GPOS"].table)
    return font


def language_feature_summary(font, table_tag="GSUB"):
    table = font[table_tag].table
    out = {}
    for sr in table.ScriptList.ScriptRecord:
        systems = []
        if sr.Script.DefaultLangSys is not None:
            systems.append(("dflt", sr.Script.DefaultLangSys))
        systems.extend((lr.LangSysTag.strip(), lr.LangSys) for lr in sr.Script.LangSysRecord)
        for lang, ls in systems:
            out[(sr.ScriptTag, lang)] = [
                table.FeatureList.FeatureRecord[i].FeatureTag for i in ls.FeatureIndex
            ]
    return out
