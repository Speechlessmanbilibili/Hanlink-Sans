from pathlib import Path
import os
from copy import deepcopy
import gc, shutil, zipfile
from fontTools.ttLib import TTFont,newTable
from fontTools.subset import Subsetter,Options
from fontTools.merge import Merger
from fontTools.otlLib.builder import buildStatTable

REPO=Path(__file__).resolve().parents[1]
WORKSPACE=Path(os.environ.get('HANLINK_BUILD_WORKSPACE', REPO.parent))
SRC=Path(os.environ.get('HANLINK_UPSTREAM_DIR', WORKSPACE/'wordfont_build'))
BRIDGE=Path(os.environ.get('HANLINK_BRIDGE_DIR', WORKSPACE/'CJKPunctBridge-v2'))
OUT=REPO; STATIC_OUT=OUT/'fonts/static'; WORK=Path(os.environ.get('HANLINK_STATIC_BUILD_DIR', WORKSPACE/'HanlinkSans-build/static'))
for p in [OUT,STATIC_OUT,WORK]: p.mkdir(parents=True,exist_ok=True)
FAMILY='Hanlink Sans'; PS='HanlinkSans'; VERSION='1.000'
WEIGHTS={100:'Thin',200:'ExtraLight',300:'Light',400:'Regular',500:'Medium',600:'SemiBold',700:'Bold',800:'ExtraBold',900:'Black'}
HFILES={w:SRC/'hanken/static'/f'HankenGrotesk-{s}.ttf' for w,s in WEIGHTS.items()}
NFILES={w:SRC/'noto/static'/f'NotoSansSC-{s}.ttf' for w,s in WEIGHTS.items()}
BFILES={w:BRIDGE/'fonts/static'/f'CJKPunctBridge-{s}.ttf' for w,s in WEIGHTS.items()}
COPYRIGHT=("Portions Copyright 2021 The Hanken Grotesk Project Authors. "
           "Portions Copyright 2014-2021 Adobe, with Reserved Font Name 'Source'. "
           "Portions Copyright 2022 Buernia, with Reserved Font Names 'Zhudou' and '煮豆'; portions Copyright 2015 Google Inc. "
           "Hanlink Sans is a modified/combined font distributed under SIL Open Font License 1.1.")
# Stable unicode split from Regular
b=TTFont(BFILES[400]); h=TTFont(HFILES[400]); n=TTFont(NFILES[400])
BC=set(b.getBestCmap()); HC=set(h.getBestCmap())-BC; NC=set(n.getBestCmap())-BC-HC
b.close(); h.close(); n.close(); print('split',len(BC),len(HC),len(NC),flush=True)

def setname(nt,nid,val):
    nt.names=[r for r in nt.names if r.nameID!=nid]; nt.setName(val,nid,3,1,0x409)
    try: val.encode('mac_roman'); nt.setName(val,nid,1,0,0)
    except Exception: pass

def set_names(f,w,style):
    nt=f['name']; legacy_family=FAMILY if w in (400,700) else f'{FAMILY} {style}'; legacy_sub='Bold' if w==700 else 'Regular'; full=FAMILY if w==400 else f'{FAMILY} {style}'
    vals={0:COPYRIGHT,1:legacy_family,2:legacy_sub,3:f'{VERSION};HanlinkBuild;{PS}-{style}',4:full,5:f'Version {VERSION}',6:f'{PS}-{style}',13:'SIL Open Font License, Version 1.1',14:'https://openfontlicense.org',16:FAMILY,17:style,25:PS}
    for k,v in vals.items(): setname(nt,k,v)
    o=f['OS/2']; o.usWeightClass=w; o.achVendID='NONE'; fs=o.fsSelection
    for bit in (0,5,6,9): fs &= ~(1<<bit)
    if w==400: fs|=1<<6
    if w==700: fs|=1<<5
    o.fsSelection=fs; f['head'].macStyle &= ~3
    if w==700: f['head'].macStyle |= 1

def subset_font(f,cps):
    o=Options(); o.layout_features=['*']; o.name_IDs=['*']; o.name_legacy=True; o.name_languages=['*']; o.notdef_glyph=True; o.notdef_outline=True; o.recommended_glyphs=True; o.glyph_names=True; o.hinting=False
    s=Subsetter(options=o); s.populate(unicodes=cps); s.subset(f); return f

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
    op=STATIC_OUT/f'{PS}-{style}.ttf'
    if op.exists() and op.stat().st_size>5_000_000: print('skip',style,flush=True); return op
    print('build',w,style,'subset',flush=True)
    hp=WORK/f'h-{w}.ttf'; np=WORK/f'n-{w}.ttf'
    hf=subset_font(TTFont(HFILES[w]),HC); nf_full=TTFont(NFILES[w]); add_vertical_to_hanken(hf,nf_full); hf.save(hp); hf.close(); nf_full.close()
    nf=subset_font(TTFont(NFILES[w]),NC); nf.save(np); nf.close()
    print('merge',style,flush=True)
    m=Merger().merge([str(BFILES[w]),str(hp),str(np)])
    no=TTFont(NFILES[w]); use_noto_metrics(m,no); set_names(m,w,style)
    try: buildStatTable(m,[dict(tag='wght',name='Weight',values=[dict(value=w,name=style,flags=0x2 if w==400 else 0)])])
    except Exception as e: print('STAT warning',style,e,flush=True)
    m.save(op,reorderTables=True); m.close(); no.close(); hp.unlink(missing_ok=True); np.unlink(missing_ok=True); gc.collect(); print('done',style,op.stat().st_size/1048576,'MiB',flush=True); return op

paths=[build(w,s) for w,s in WEIGHTS.items()]
# compatibility checks
orders=[]
for p in paths:
    f=TTFont(p,lazy=True); orders.append(f.getGlyphOrder()); f.close()
assert all(o==orders[0] for o in orders[1:]),'glyph orders differ'
reg=TTFont(STATIC_OUT/f'{PS}-Regular.ttf'); cm=reg.getBestCmap(); tags=sorted(set(r.FeatureTag for r in reg['GSUB'].table.FeatureList.FeatureRecord)); print('validate static',len(reg.getGlyphOrder()),len(cm),'vhea' in reg,'vmtx' in reg,len(reg['vmtx'].metrics),tags,flush=True); reg.close()
