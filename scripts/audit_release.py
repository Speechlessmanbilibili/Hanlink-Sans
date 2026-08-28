from pathlib import Path
from fontTools.ttLib import TTFont
from language_systems import (
    CJK_LANGUAGE_TAGS,
    HANKEN_SHARED_PUNCTUATION,
    WESTERN_LANGUAGE_SYSTEMS,
    WESTERN_SCRIPT_TAGS,
)
from font_metadata import audit_metadata

DASHES=(0x2014,0x2E3A,0x2E3B)
HANKEN_CORE={'aalt','case','ccmp','dlig','dnom','frac','liga','numr','ordn','ss01','ss02','ss03','sups'}
ZHS_CORE={'ccmp','dlig','fwid','hwid','pwid','ruby','vert','vrt2'}
CJK_CORE={'ccmp','dlig','locl','vert','vrt2'}

def _script(table, tag):
    return next((sr.Script for sr in table.ScriptList.ScriptRecord if sr.ScriptTag==tag),None)

def _langsys(table, script, lang=None):
    sc=_script(table,script)
    if sc is None:return None
    if lang is None:return sc.DefaultLangSys
    wanted=lang.ljust(4)[:4]
    return next((lr.LangSys for lr in sc.LangSysRecord if lr.LangSysTag==wanted),None)

def _tags(table,ls):
    if ls is None:return []
    return [table.FeatureList.FeatureRecord[i].FeatureTag for i in ls.FeatureIndex]

def _bbox(font,glyph):
    g=font['glyf'][glyph];g.recalcBounds(font['glyf'])
    return g.xMin,g.yMin,g.xMax,g.yMax

def _single_maps(table,ls,tag):
    out={}
    if ls is None:return out
    for fi in ls.FeatureIndex:
        fr=table.FeatureList.FeatureRecord[fi]
        if fr.FeatureTag!=tag:continue
        for li in fr.Feature.LookupListIndex:
            lk=table.LookupList.Lookup[li]
            for st in lk.SubTable:
                typ=lk.LookupType
                if typ==7:typ=st.ExtensionLookupType;st=st.ExtSubTable
                if typ==1 and hasattr(st,'mapping'):out.update(st.mapping)
    return out

def _all_langsystems(table):
    for sr in table.ScriptList.ScriptRecord:
        if sr.Script.DefaultLangSys is not None:yield sr.ScriptTag,'dflt',sr.Script.DefaultLangSys
        for lr in sr.Script.LangSysRecord:yield sr.ScriptTag,lr.LangSysTag.strip(),lr.LangSys

def _glyph_signature(font,glyph):
    g=font['glyf'][glyph]
    coords,end_pts,flags=g.getCoordinates(font['glyf'])
    return tuple(coords),tuple(end_pts),bytes(flags),font['hmtx'].metrics[glyph]

def audit(path):
    f=TTFont(path); cmap=f.getBestCmap()
    if 'fvar' in f:
        unique_id='HanlinkSans-Italic-VF' if 'Italic' in path.name else 'HanlinkSans-VF'
    else:
        unique_id=path.stem
    audit_metadata(f,unique_id)
    assert 'vhea' in f and 'vmtx' in f
    assert 'prep' in f, (path, 'missing shared upstream TrueType prep program')
    assert set(('DFLT','latn','hani','kana','grek','cyrl','bopo')) <= {sr.ScriptTag for sr in f['GSUB'].table.ScriptList.ScriptRecord}
    assert 'bopo' in {sr.ScriptTag for sr in f['GPOS'].table.ScriptList.ScriptRecord}
    for table_tag in ('GSUB','GPOS'):
        table=f[table_tag].table
        feature_tags=[record.FeatureTag for record in table.FeatureList.FeatureRecord]
        assert feature_tags==sorted(feature_tags),(path,table_tag,'FeatureList is not sorted')
        for script,lang,ls in _all_langsystems(table):
            tags=_tags(table,ls)
            assert len(tags)==len(set(tags)),(path,table_tag,script,lang,'duplicate feature tags',tags)
    g=f['GSUB'].table
    digit_sources={cmap[cp] for cp in range(0x30,0x3A)}
    assert len(digit_sources)==10,(path,'ASCII digits do not have ten distinct public Hanken glyphs')
    for script,lang,ls in _all_langsystems(g):
        locl=_single_maps(g,ls,'locl')
        assert not digit_sources & set(locl),(path,script,lang,'locl must not replace Hanken digits')
    latn_default=set(_tags(g,_langsys(g,'latn',None)))
    latn_eng=set(_tags(g,_langsys(g,'latn','ENG ')))
    latn_zhs=set(_tags(g,_langsys(g,'latn','ZHS ')))
    assert HANKEN_CORE|ZHS_CORE|{'locl'} <= latn_default
    assert HANKEN_CORE|{'locl'} <= latn_eng
    assert HANKEN_CORE|ZHS_CORE|{'locl'} <= latn_zhs
    assert ZHS_CORE|{'locl'} <= set(_tags(g,_langsys(g,'hani','ZHS ')))
    assert len({cmap[cp] for cp in HANKEN_SHARED_PUNCTUATION})==len(HANKEN_SHARED_PUNCTUATION)
    western_targets=None
    for script in WESTERN_SCRIPT_TAGS:
        default_locl=_single_maps(g,_langsys(g,script,None),'locl')
        for lang in WESTERN_LANGUAGE_SYSTEMS[script]:
            ls=_langsys(g,script,lang)
            assert ls is not None,(path,script,lang,'missing Western LangSys')
            locl=_single_maps(g,ls,'locl')
            targets=[]
            for cp in HANKEN_SHARED_PUNCTUATION:
                source=cmap[cp];target=locl.get(source)
                assert target and target!=source,(path,script,lang,hex(cp),'missing Hanken locl')
                assert default_locl.get(source,source)!=target,(path,script,lang,hex(cp),'default leaked Hanken')
                targets.append(target)
            if western_targets is None:western_targets=tuple(targets)
            else:assert tuple(targets)==western_targets,(path,script,lang,'inconsistent Hanken targets')
    for lang in CJK_LANGUAGE_TAGS:
        ls=_langsys(g,'DFLT',lang)
        assert ls is not None,(path,lang,'missing CJK LangSys')
        assert CJK_CORE <= set(_tags(g,ls)),(path,lang,_tags(g,ls))
        locl=_single_maps(g,ls,'locl')
        assert locl.get(cmap[0x2014],cmap[0x2014])!=western_targets[HANKEN_SHARED_PUNCTUATION.index(0x2014)],(path,lang,'CJK dash leaked Hanken')
    for script,cp in (('grek',0x0301),('grek',0x0394),('cyrl',0x0301),('bopo',0x02C7),('bopo',0x02D9)):
        if cp not in cmap:continue
        mp=_single_maps(g,_langsys(g,script,None),'ccmp')
        assert cmap[cp] in mp and mp[cmap[cp]]!=cmap[cp],(path,script,hex(cp),'missing Noto script remap')
    for cp in DASHES:
        glyph=cmap[cp];x0,y0,x1,y1=_bbox(f,glyph)
        assert x1-x0>y1-y0,(path,hex(cp),'default horizontal dash is not horizontal')
    if 'fvar' in f:
        axis=next(a for a in f['fvar'].axes if a.axisTag=='wght')
        assert (axis.minValue,axis.defaultValue,axis.maxValue)==(100.0,400.0,900.0)
        assert len(f['fvar'].instances)==9
    italic=bool(f['OS/2'].fsSelection & 1)
    regular=bool(f['OS/2'].fsSelection & (1<<6))
    if italic:
        assert not regular,(path,'italic and regular fsSelection bits conflict')
        assert f['head'].macStyle & 2,(path,'italic macStyle missing')
        assert f['post'].italicAngle<0,(path,'italicAngle not negative')
        sub=f['name'].getDebugName(2)
        assert sub and sub.endswith('Italic'),(path,'subfamily',sub)
    f.close()

def audit_hanken_provenance(path,source_path):
    f=TTFont(path);h=TTFont(source_path)
    cmap=f.getBestCmap();hcmap=h.getBestCmap()
    bridge_shared=set(HANKEN_SHARED_PUNCTUATION)
    for cp in range(0x30,0x3A):
        assert _glyph_signature(f,cmap[cp])==_glyph_signature(h,hcmap[cp]),(hex(cp),'digit is not exact Hanken outline/metrics')
    for cp in sorted(set(hcmap)-bridge_shared):
        assert _glyph_signature(f,cmap[cp])==_glyph_signature(h,hcmap[cp]),hex(cp)
    locl=_single_maps(f['GSUB'].table,_langsys(f['GSUB'].table,'latn','ENG '),'locl')
    for cp in HANKEN_SHARED_PUNCTUATION:
        assert _glyph_signature(f,locl[cmap[cp]])==_glyph_signature(h,hcmap[cp]),hex(cp)
    f.close();h.close()

if __name__=='__main__':
    import sys
    root=Path(__file__).resolve().parents[1]
    hanken=root/'sources/hanken/static/HankenGrotesk-Regular.ttf'
    hanken_italic=root/'sources/hanken/static/HankenGrotesk-Italic-Regular.ttf'
    for arg in sys.argv[1:]:
        path=Path(arg);audit(path)
        if hanken.exists() and path.name in {'HanlinkSans-Regular.ttf','HanlinkSans-Variable.ttf'}:
            audit_hanken_provenance(path,hanken)
        if hanken_italic.exists() and path.name in {'HanlinkSans-Italic.ttf','HanlinkSans-Italic-Variable.ttf'}:
            audit_hanken_provenance(path,hanken_italic)
        print('OK',arg)
