from pathlib import Path
import os
from copy import deepcopy
import gc, shutil
from fontTools.ttLib import TTFont,newTable
from fontTools.subset import Subsetter,Options
from fontTools.varLib.instancer import instantiateVariableFont,AxisTriple
from fontTools.merge import Merger,computeMegaGlyphOrder
from fontTools.ttLib.tables._f_v_a_r import Axis,NamedInstance
from fontTools.otlLib.builder import buildStatTable

REPO=Path(__file__).resolve().parents[1]
WORKSPACE=Path(os.environ.get('HANLINK_BUILD_WORKSPACE', REPO.parent))
SRC=Path(os.environ.get('HANLINK_UPSTREAM_DIR', WORKSPACE/'wordfont_build'))
BRIDGE=Path(os.environ.get('HANLINK_BRIDGE_DIR', WORKSPACE/'CJKPunctBridge-v2'))
OUT=REPO/'fonts/variable'; WORK=Path(os.environ.get('HANLINK_VF_BUILD_DIR', WORKSPACE/'HanlinkSans-build/vf'))
OUT.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True)
FAMILY='Hanlink Sans'; PS='HanlinkSans'; VERSION='1.000'
WEIGHTS={100:'Thin',200:'ExtraLight',300:'Light',400:'Regular',500:'Medium',600:'SemiBold',700:'Bold',800:'ExtraBold',900:'Black'}
HVAR=SRC/'hanken/HankenGrotesk-VariableFont_wght.ttf'; NVAR=SRC/'noto/NotoSansSC-VariableFont_wght.ttf'; BVAR=BRIDGE/'fonts/variable/CJKPunctBridge-Variable.ttf'
HREG=SRC/'hanken/static/HankenGrotesk-Regular.ttf'; NREG=SRC/'noto/static/NotoSansSC-Regular.ttf'; BREG=BRIDGE/'fonts/static/CJKPunctBridge-Regular.ttf'
COPYRIGHT=("Portions Copyright 2021 The Hanken Grotesk Project Authors. Portions Copyright 2014-2021 Adobe, with Reserved Font Name 'Source'. Portions Copyright 2022 Buernia, with Reserved Font Names 'Zhudou' and '煮豆'; portions Copyright 2015 Google Inc. Hanlink Sans is a modified/combined font distributed under SIL Open Font License 1.1.")
b=TTFont(BVAR); h=TTFont(HVAR); n=TTFont(NVAR); BC=set(b.getBestCmap()); HC=set(h.getBestCmap())-BC; NC=set(n.getBestCmap())-BC-HC; b.close();h.close();n.close(); print('split',len(BC),len(HC),len(NC),flush=True)

def subset(f,cps,layout=True):
    o=Options(); o.layout_features=['*'] if layout else []; o.name_IDs=['*'];o.name_legacy=True;o.name_languages=['*'];o.notdef_glyph=True;o.notdef_outline=True;o.recommended_glyphs=True;o.glyph_names=True;o.hinting=False
    s=Subsetter(options=o);s.populate(unicodes=cps);s.subset(f);return f

def subset_var(f,cps,path):
    if 'gvar' in f:
        gv=f['gvar'].variations
        for gn in f.getGlyphOrder(): gv.setdefault(gn,[])
    subset(f,cps,True)
    for t in ('HVAR','VVAR','MVAR','avar','STAT','BASE','GDEF','GPOS','GSUB','vhea','vmtx','VORG'):
        if t in f: del f[t]
    f.save(path);f.close()

def prep_var():
    bp=WORK/'bridge-vf.ttf'; hp=WORK/'hanken-vf.ttf'; np=WORK/'noto-vf.ttf'
    if not bp.exists(): print('bridge var subset',flush=True);subset_var(TTFont(BVAR),BC,bp)
    if not hp.exists(): print('hanken var subset',flush=True);subset_var(TTFont(HVAR),HC,hp)
    if not np.exists(): print('noto var rebase/subset',flush=True); nf=instantiateVariableFont(TTFont(NVAR),{'wght':AxisTriple(100,400,900)},inplace=False,optimize=False);subset_var(nf,NC,np)
    return [bp,hp,np]

def add_vertical_to_hanken(h,noto):
    h['vhea']=deepcopy(noto['vhea']);vm=newTable('vmtx');metrics={};nc=noto.getBestCmap();nvm=noto['vmtx'].metrics;hc=h.getBestCmap();rev={}
    for cp,g in hc.items():rev.setdefault(g,cp)
    glyf=h['glyf']
    for gn in h.getGlyphOrder():
        cp=rev.get(gn)
        if cp is not None and cp in nc: metrics[gn]=nvm[nc[cp]]
        else:
            g=glyf[gn]
            try:g.recalcBounds(glyf);ymax=getattr(g,'yMax',0)
            except:ymax=0
            metrics[gn]=(1000,880-ymax)
    vm.metrics=metrics;h['vmtx']=vm;h['vhea'].numberOfVMetrics=len(h.getGlyphOrder())

def setname(nt,nid,val):
    nt.names=[r for r in nt.names if r.nameID!=nid];nt.setName(val,nid,3,1,0x409)
    try:val.encode('mac_roman');nt.setName(val,nid,1,0,0)
    except:pass

def set_names(f):
    nt=f['name'];vals={0:COPYRIGHT,1:FAMILY,2:'Regular',3:f'{VERSION};HanlinkBuild;{PS}-VF',4:FAMILY,5:f'Version {VERSION}',6:PS,13:'SIL Open Font License, Version 1.1',14:'https://openfontlicense.org',16:FAMILY,17:'Regular',25:PS}
    for k,v in vals.items():setname(nt,k,v)
    o=f['OS/2'];o.usWeightClass=400;o.achVendID='NONE';fs=o.fsSelection
    for bit in (0,5,6,9):fs&=~(1<<bit)
    fs|=1<<6;o.fsSelection=fs;f['head'].macStyle&=~3

def use_noto_metrics(f,n):
    f['hhea'].ascent=n['hhea'].ascent;f['hhea'].descent=n['hhea'].descent;f['hhea'].lineGap=n['hhea'].lineGap
    for a in ('sTypoAscender','sTypoDescender','sTypoLineGap','usWinAscent','usWinDescent','sxHeight','sCapHeight'):
        if hasattr(n['OS/2'],a):setattr(f['OS/2'],a,getattr(n['OS/2'],a))
    if 'vhea' in f:
        for a in ('ascent','descent','lineGap','caretSlopeRise','caretSlopeRun','caretOffset','metricDataFormat'):
            if hasattr(n['vhea'],a):setattr(f['vhea'],a,getattr(n['vhea'],a))

varpaths=prep_var();orig=[];ren=[]
for p in varpaths:
    f=TTFont(p,lazy=True);o=list(f.getGlyphOrder());f.close();orig.append(o);ren.append(list(o))
dummy=Merger();computeMegaGlyphOrder(dummy,ren);maps=[dict(zip(o,r)) for o,r in zip(orig,ren)]
# Recreate unsaved 400 base so glyph names exactly match merge's mega order.
print('build unsaved Regular base',flush=True)
bp=WORK/'bridge-400.ttf'; hp=WORK/'hanken-400.ttf'; np=WORK/'noto-400.ttf'
if not bp.exists(): shutil.copy(BREG,bp)
if not hp.exists():
    hf=subset(TTFont(HREG),HC,True); nf_full=TTFont(NREG); add_vertical_to_hanken(hf,nf_full); hf.save(hp); hf.close(); nf_full.close()
if not np.exists():
    nf=subset(TTFont(NREG),NC,True); nf.save(np); nf.close()
nf_full=TTFont(NREG); base=Merger().merge([str(bp),str(hp),str(np)]); use_noto_metrics(base,nf_full); set_names(base); nf_full.close()
print('orders',len(base.getGlyphOrder()),len(dummy.glyphOrder),base.getGlyphOrder()==dummy.glyphOrder,flush=True)
assert base.getGlyphOrder()==dummy.glyphOrder
print('combine gvar',flush=True);combined={}
for p,mp in zip(varpaths,maps):
    f=TTFont(p);gv=f['gvar'].variations;count=0
    for old,vs in gv.items():
        new=mp.get(old)
        if new is not None and vs:combined[new]=deepcopy(vs);count+=1
    print(p.name,count,flush=True);f.close();gc.collect()
gvar=newTable('gvar');gvar.version=1;gvar.reserved=0;gvar.variations=combined;base['gvar']=gvar
fv=newTable('fvar');fv.axes=[];fv.instances=[];axis=Axis();axis.axisTag='wght';axis.minValue=100.;axis.defaultValue=400.;axis.maxValue=900.;axis.flags=0;axis.axisNameID=base['name'].addName('Weight',platforms=((3,1,0x409),(1,0,0)));fv.axes.append(axis)
for w,s in WEIGHTS.items():
    ins=NamedInstance();ins.subfamilyNameID=base['name'].addName(s,platforms=((3,1,0x409),(1,0,0)));ins.postscriptNameID=0xFFFF;ins.flags=0;ins.coordinates={'wght':float(w)};fv.instances.append(ins)
base['fvar']=fv
try:buildStatTable(base,[dict(tag='wght',name='Weight',values=[dict(value=w,name=s,flags=0x2 if w==400 else 0) for w,s in WEIGHTS.items()])])
except Exception as e:print('STAT',e,flush=True)
out=OUT/f'{PS}-Variable.ttf';base.save(out,reorderTables=True);base.close();print('saved',out.stat().st_size/1048576,'MiB',flush=True)
# validate widths at endpoints/default against static builds
vf0=TTFont(out);print('validate VF',len(vf0.getGlyphOrder()),'v', 'vhea' in vf0,'vmtx' in vf0,'gvar',sum(bool(v) for v in vf0['gvar'].variations.values()),[(a.minValue,a.defaultValue,a.maxValue) for a in vf0['fvar'].axes],flush=True);vf0.close()
for w,s in [(100,'Thin'),(400,'Regular'),(900,'Black')]:
    vf=TTFont(out);inst=instantiateVariableFont(vf,{'wght':w},inplace=False,optimize=True,static=True);st=TTFont(REPO/f'fonts/static/{PS}-{s}.ttf');ic=inst.getBestCmap();sc=st.getBestCmap();checks=[]
    for cp in (0x41,0x61,0x4E2D,0xFF0C,0x2014):checks.append((hex(cp),inst['hmtx'].metrics[ic[cp]],st['hmtx'].metrics[sc[cp]]))
    print('widthcheck',w,checks,flush=True);inst.close();vf.close();st.close()
