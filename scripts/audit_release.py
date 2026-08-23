from pathlib import Path
from fontTools.ttLib import TTFont

DASHES=(0x2014,0x2E3A,0x2E3B)
WESTERN_PUNCT=(0x00B7,0x2013,0x2014,0x2018,0x2019,0x201C,0x201D,0x2026)
HANKEN_CORE={'aalt','case','ccmp','dlig','dnom','frac','liga','numr','ordn','ss01','ss02','ss03','sups'}
ZHS_CORE={'ccmp','dlig','fwid','hwid','pwid','ruby','vert','vrt2'}

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
                if typ==7:st=st.ExtSubTable;typ=st.ExtensionLookupType
                if typ==1 and hasattr(st,'mapping'):out.update(st.mapping)
    return out

def _all_langsystems(table):
    for sr in table.ScriptList.ScriptRecord:
        if sr.Script.DefaultLangSys is not None:yield sr.ScriptTag,'dflt',sr.Script.DefaultLangSys
        for lr in sr.Script.LangSysRecord:yield sr.ScriptTag,lr.LangSysTag.strip(),lr.LangSys

def audit(path):
    f=TTFont(path); cmap=f.getBestCmap()
    assert 'vhea' in f and 'vmtx' in f
    assert 'prep' in f, (path, 'missing shared upstream TrueType prep program')
    assert set(('DFLT','latn','hani','kana','grek','cyrl','bopo')) <= {sr.ScriptTag for sr in f['GSUB'].table.ScriptList.ScriptRecord}
    assert 'bopo' in {sr.ScriptTag for sr in f['GPOS'].table.ScriptList.ScriptRecord}
    for table_tag in ('GSUB','GPOS'):
        table=f[table_tag].table
        for script,lang,ls in _all_langsystems(table):
            tags=_tags(table,ls)
            assert len(tags)==len(set(tags)),(path,table_tag,script,lang,'duplicate feature tags',tags)
    g=f['GSUB'].table
    latn_default=set(_tags(g,_langsys(g,'latn',None)))
    latn_eng=set(_tags(g,_langsys(g,'latn','ENG ')))
    latn_zhs=set(_tags(g,_langsys(g,'latn','ZHS ')))
    assert HANKEN_CORE|{'locl'} <= latn_default
    assert HANKEN_CORE|{'locl'} <= latn_eng
    assert HANKEN_CORE|ZHS_CORE|{'locl'} <= latn_zhs
    assert ZHS_CORE|{'locl'} <= set(_tags(g,_langsys(g,'hani','ZHS ')))
    latn_locl=_single_maps(g,_langsys(g,'latn',None),'locl')
    for cp in WESTERN_PUNCT:
        assert cmap[cp] in latn_locl and latn_locl[cmap[cp]]!=cmap[cp],(path,hex(cp),'missing Western locl')
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
    f.close()

if __name__=='__main__':
    import sys
    for arg in sys.argv[1:]:
        audit(Path(arg));print('OK',arg)
