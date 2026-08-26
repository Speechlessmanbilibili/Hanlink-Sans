from pathlib import Path
import os
import math
from copy import deepcopy
import gc
from fontTools.ttLib import TTFont,newTable
from fontTools.subset import Subsetter,Options
from fontTools.merge import Merger,computeMegaGlyphOrder
from fontTools.otlLib.builder import buildStatTable
from layout_compat import fix_hanlink_language_systems
from font_metadata import apply_binary_metadata, project_names

REPO=Path(__file__).resolve().parents[1]
WORKSPACE=Path(os.environ.get('HANLINK_BUILD_WORKSPACE', REPO.parent))
SRC=Path(os.environ.get('HANLINK_UPSTREAM_DIR', REPO/'sources'))
BRIDGE=Path(os.environ.get('HANLINK_BRIDGE_DIR', REPO.parent/'CJK-Punct-Bridge'))
OUT=REPO; STATIC_OUT=OUT/'fonts/static'; WORK=Path(os.environ.get('HANLINK_STATIC_BUILD_DIR', REPO/'build/static'))
for p in [OUT,STATIC_OUT,WORK]: p.mkdir(parents=True,exist_ok=True)
FAMILY='Hanlink Sans'; PS='HanlinkSans'
WEIGHTS={100:'Thin',200:'ExtraLight',300:'Light',400:'Regular',500:'Medium',600:'SemiBold',700:'Bold',800:'ExtraBold',900:'Black'}
# Synthetic italic: Hanken supplies true italic Latin designs; CJK (Noto SC and
# the punctuation bridge) has no true italic, so it gets a uniform 10-degree
# y-shear, the usual synthetic slant.
ITALIC=os.environ.get('HANLINK_ITALIC')=='1'
SLANT_DEG=10.0
SLANT=math.tan(math.radians(SLANT_DEG))
HFILES={w:SRC/'hanken/static'/(f'HankenGrotesk-Italic-{s}.ttf' if ITALIC else f'HankenGrotesk-{s}.ttf') for w,s in WEIGHTS.items()}
NFILES={w:SRC/'noto/static'/f'NotoSansSC-{s}.ttf' for w,s in WEIGHTS.items()}
BFILES={w:BRIDGE/'fonts/static'/(f'CJKPunctBridge-Italic.ttf' if (ITALIC and w==400) else f'CJKPunctBridge-{s}{"Italic" if ITALIC else ""}.ttf') for w,s in WEIGHTS.items()}
# Stable unicode split from Regular
b=TTFont(BFILES[400]); h=TTFont(HFILES[400]); n=TTFont(NFILES[400])
BC=set(b.getBestCmap()); HALL=set(h.getBestCmap()); NALL=set(n.getBestCmap()); HC=HALL; NC=NALL
b.close(); h.close(); n.close(); print('split',len(BC),len(HC),len(NC),flush=True)

def shear_font(font, slant=SLANT, slant_deg=SLANT_DEG):
    """Synthetic italic: y-shear every outline so x' = x + y*slant.

    Simple glyphs keep their exact point structure, flags, and end points --
    only the coordinates are transformed, so varLib still sees interpolatable
    masters.  Composite glyphs are decomposed (identical on every master).
    Advance widths stay unchanged while the left side bearing is recomputed
    from the new bounds; vertical metrics are untouched because the shear does
    not move y.
    """
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    glyph_set = font.getGlyphSet()
    glyf = font['glyf']
    hmtx = font['hmtx']
    for name in font.getGlyphOrder():
        glyph = glyf[name]
        if glyph is None or glyph.numberOfContours == 0:
            continue
        if glyph.numberOfContours > 0:
            coords = glyph.coordinates
            for i, (x, y) in enumerate(coords):
                coords[i] = (x + y * slant, y)
        else:
            rec = DecomposingRecordingPen(glyph_set)
            glyph_set[name].draw(rec)
            pen = TTGlyphPen(glyph_set)
            rec.replay(pen)
            glyf[name] = pen.glyph()
        glyph = glyf[name]
        glyph.recalcBounds(glyf)
        adv = hmtx.metrics[name][0]
        hmtx.metrics[name] = (adv, getattr(glyph, 'xMin', 0))
    font['post'].italicAngle = -slant_deg

def setname(nt,nid,val):
    nt.names=[r for r in nt.names if r.nameID!=nid]; nt.setName(val,nid,3,1,0x409)
    try: val.encode('mac_roman'); nt.setName(val,nid,1,0,0)
    except Exception: pass

def set_names(f,w,style,italic=False):
    nt=f['name']
    if italic:
        sub='Italic' if w==400 else f'{style} Italic'
        legacy_family=FAMILY if w in (400,700) else f'{FAMILY} {style}'
        legacy_sub='Bold Italic' if w==700 else 'Italic'
        full=FAMILY if w==400 else f'{FAMILY} {style}'
        full=f'{full} Italic'
        unique=f'{PS}-Italic' if w==400 else f'{PS}-{style}Italic'
    else:
        sub='Bold' if w==700 else 'Regular'
        legacy_family=FAMILY if w in (400,700) else f'{FAMILY} {style}'
        legacy_sub=sub
        full=FAMILY if w==400 else f'{FAMILY} {style}'
        unique=f'{PS}-{style}'
    vals={**project_names(unique),1:legacy_family,2:legacy_sub,4:full,
          6:unique,16:FAMILY,17:(sub if italic else style),25:PS}
    for k,v in vals.items(): setname(nt,k,v)
    apply_binary_metadata(f)
    o=f['OS/2']; o.usWeightClass=w; fs=o.fsSelection
    for bit in (0,5,6,9): fs &= ~(1<<bit)
    if italic: fs|=1<<0
    if w==400 and not italic: fs|=1<<6
    if w==700: fs|=1<<5
    o.fsSelection=fs; f['head'].macStyle &= ~3
    if w==700: f['head'].macStyle |= 1
    if italic: f['head'].macStyle |= 2

def remove_cmap_codepoints(f,cps):
    if 'cmap' not in f: return
    for table in f['cmap'].tables:
        if hasattr(table,'cmap'):
            for cp in cps: table.cmap.pop(cp,None)

def subset_font(f,cps):
    o=Options(); o.layout_features=['*']; o.name_IDs=['*']; o.name_legacy=True; o.name_languages=['*']; o.notdef_glyph=True; o.notdef_outline=True; o.recommended_glyphs=True; o.glyph_names=True; o.hinting=True
    s=Subsetter(options=o); s.populate(unicodes=cps); s.subset(f); return f

def drop_unmergeable_base_varstore(f):
    # Google Fonts Noto CJK static instances retain a BASE ItemVariationStore.
    # fontTools.merge cannot combine source-specific BASE variation stores, and
    # Hanlink normalizes to Noto metrics instead of publishing that source table.
    if 'BASE' in f: del f['BASE']

def add_vertical_to_hanken(h,noto):
    h['vhea']=deepcopy(noto['vhea']); vm=newTable('vmtx'); metrics={}
    nc=noto.getBestCmap(); nvm=noto['vmtx'].metrics; hc=h.getBestCmap(); reverse={}
    for cp,g in hc.items(): reverse.setdefault(g,cp)
    glyf=h['glyf']; default_origin=880
    for gname in h.getGlyphOrder():
        cp=reverse.get(gname)
        if cp is not None and cp in nc: metrics[gname]=nvm[nc[cp]]
        else:
            g=glyf[gname]
            try: g.recalcBounds(glyf); ymax=getattr(g,'yMax',0)
            except Exception: ymax=0
            metrics[gname]=(1000,default_origin-ymax)
    vm.metrics=metrics; h['vmtx']=vm; h['vhea'].numberOfVMetrics=len(h.getGlyphOrder())

def use_noto_metrics(f,n):
    f['hhea'].ascent=n['hhea'].ascent; f['hhea'].descent=n['hhea'].descent; f['hhea'].lineGap=n['hhea'].lineGap
    o,no=f['OS/2'],n['OS/2']
    for a in ('sTypoAscender','sTypoDescender','sTypoLineGap','usWinAscent','usWinDescent','sxHeight','sCapHeight'):
        if hasattr(no,a): setattr(o,a,getattr(no,a))
    if 'vhea' in f and 'vhea' in n:
        for a in ('ascent','descent','lineGap','advanceHeightMax','minTopSideBearing','minBottomSideBearing','yMaxExtent','caretSlopeRise','caretSlopeRun','caretOffset','metricDataFormat'):
            if hasattr(n['vhea'],a): setattr(f['vhea'],a,getattr(n['vhea'],a))

def build(w,style):
    op=STATIC_OUT/(f'{PS}-Italic.ttf' if (ITALIC and w==400) else f'{PS}-{style}{"Italic" if ITALIC else ""}.ttf')
    if os.environ.get('HANLINK_REUSE_STATIC')=='1' and op.exists() and op.stat().st_size>5_000_000:
        print('reuse',style,flush=True); return op
    print('build',w,style,'subset',flush=True)
    bp=WORK/f'b-{w}.ttf'; hp=WORK/f'h-{w}.ttf'; np=WORK/f'n-{w}.ttf'
    bf=TTFont(BFILES[w]); drop_unmergeable_base_varstore(bf); bf.save(bp); bf.close()
    hf=subset_font(TTFont(HFILES[w]),HC); hanken_pre_order=list(hf.getGlyphOrder()); remove_cmap_codepoints(hf,BC); nf_full=TTFont(NFILES[w]); add_vertical_to_hanken(hf,nf_full); hf.save(hp); hf.close(); nf_full.close()
    hsaved=TTFont(hp,lazy=True); hanken_saved_order=list(hsaved.getGlyphOrder()); hsaved.close()
    hanken_orig_to_saved=dict(zip(hanken_pre_order,hanken_saved_order))
    nf=subset_font(TTFont(NFILES[w]),NC); noto_pre_order=list(nf.getGlyphOrder()); remove_cmap_codepoints(nf,BC|HALL); drop_unmergeable_base_varstore(nf)
    if ITALIC:
        shear_font(nf)
    nf.save(np); nf.close()
    nsaved=TTFont(np,lazy=True); noto_saved_order=list(nsaved.getGlyphOrder()); nsaved.close()
    noto_orig_to_saved=dict(zip(noto_pre_order,noto_saved_order))
    print('merge',style,flush=True)
    source_paths=[bp,hp,np]; orig=[]; ren=[]
    for sp in source_paths:
        sf=TTFont(sp,lazy=True); order=list(sf.getGlyphOrder()); sf.close(); orig.append(order); ren.append(list(order))
    dummy=Merger(); computeMegaGlyphOrder(dummy,ren); maps=[dict(zip(o,r)) for o,r in zip(orig,ren)]
    hfull=TTFont(HFILES[w],lazy=True); hfullcm=dict(hfull.getBestCmap()); hfull.close()
    hanken_hidden={}
    for cp in BC:
        original=hfullcm.get(cp); saved=hanken_orig_to_saved.get(original) if original else None
        if saved in maps[1]: hanken_hidden[cp]=maps[1][saved]
    noto_glyph_map={
        original:maps[2][saved]
        for original,saved in noto_orig_to_saved.items() if saved in maps[2]
    }
    m=Merger().merge([str(x) for x in source_paths])
    no=TTFont(NFILES[w]); hs=TTFont(HFILES[w]); fix_hanlink_language_systems(m,hanken_hidden,hs,no,noto_glyph_map,HALL-BC,BC)
    if 'prep' in hs:
        m['prep']=deepcopy(hs['prep'])
    use_noto_metrics(m,no); set_names(m,w,style,italic=ITALIC)
    stat_axes=[dict(tag='wght',name='Weight',values=[dict(value=w,name=style,flags=0x2 if w==400 else 0)])]
    if ITALIC:
        stat_axes.append(dict(tag='ital',name='Italic',values=[dict(value=1,name='Italic')]))
    try: buildStatTable(m,stat_axes)
    except Exception as e: print('STAT warning',style,e,flush=True)
    m.save(op,reorderTables=True); m.close(); no.close(); hs.close(); bp.unlink(missing_ok=True); hp.unlink(missing_ok=True); np.unlink(missing_ok=True); gc.collect(); print('done',style,op.stat().st_size/1048576,'MiB',flush=True); return op

only=os.environ.get('HANLINK_ONLY_WEIGHT')
selected=WEIGHTS if not only else {int(only):WEIGHTS[int(only)]}
paths=[build(w,s) for w,s in selected.items()]
orders=[]
for p in paths:
    f=TTFont(p,lazy=True); orders.append(f.getGlyphOrder()); f.close()
assert all(o==orders[0] for o in orders[1:]),'glyph orders differ'
reg_path=STATIC_OUT/(f'{PS}-Italic.ttf' if ITALIC else f'{PS}-Regular.ttf')
if reg_path.exists():
    reg=TTFont(reg_path); cm=reg.getBestCmap(); tags=sorted(set(r.FeatureTag for r in reg['GSUB'].table.FeatureList.FeatureRecord)); print('validate static',len(reg.getGlyphOrder()),len(cm),'vhea' in reg,'vmtx' in reg,len(reg['vmtx'].metrics),tags,flush=True); reg.close()
