"""Mechanical sprite extraction, caption typesetting, and animated WebP packaging.
Character drawings and all pose changes are generated with built-in image_gen.
"""
from pathlib import Path
import csv, json, struct, shutil, argparse, html, os
from PIL import Image, ImageDraw, ImageFont, ImageCms, ImageChops

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'prompts.json').read_text())
FONT=os.environ.get('SPRITE_FONT', '/System/Library/Fonts/AppleSDGothicNeo.ttc')
FONT_INDEX=int(os.environ.get('SPRITE_FONT_INDEX', '6' if FONT.endswith('AppleSDGothicNeo.ttc') else '0'))
ICC=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
EXIF=Image.Exif()
EXIF[282]=72; EXIF[283]=72; EXIF[296]=2; EXIF[40961]=1
S=3

def save_png(im,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path,dpi=(72,72),icc_profile=ICC,optimize=True)

def label(caption):
    im=Image.new('RGBA',(360*S,360*S))
    d=ImageDraw.Draw(im)
    lines=caption.split('\n')
    size=37 if len(lines)==1 else 32
    while True:
        f=ImageFont.truetype(FONT,size*S,index=FONT_INDEX)
        widths=[d.textbbox((0,0),x,font=f,stroke_width=4*S)[2] for x in lines]
        if max(widths)<=314*S:break
        size-=1
    lineh=(size+5)*S
    top=(31 if len(lines)==1 else 20)*S
    for i,line in enumerate(lines):
        box=d.textbbox((0,0),line,font=f)
        x=(360*S-(box[2]-box[0]))/2-box[0]
        y=top+i*lineh-box[1]
        d.text((x,y),line,font=f,fill='#35291f',stroke_width=4*S,stroke_fill='white')
    return im.resize((360,360),Image.Resampling.LANCZOS)

def riff_info(path):
    data=path.read_bytes(); assert data[:4]==b'RIFF' and data[8:12]==b'WEBP'
    out={'durations_ms':[],'chunks':[]}; off=12
    while off<len(data):
        kind=data[off:off+4]; n=int.from_bytes(data[off+4:off+8],'little'); chunk=data[off+8:off+8+n]
        out['chunks'].append(kind.decode())
        if kind==b'ANIM':out['loop']=int.from_bytes(chunk[4:6],'little');out['background_bgra']=list(chunk[:4])
        if kind==b'ANMF':out['durations_ms'].append(int.from_bytes(chunk[12:15],'little'))
        off+=8+n+(n%2)
    return out

def process(item):
    stem=item['id']; src=ROOT/'source-sheets'/f'{stem}.png'
    if not src.exists():return None
    sheet=Image.open(src).convert('RGBA'); w,h=sheet.size
    cells=[]; boxes=[]
    for j in range(6):
        x=j%3;y=j//3
        cell=sheet.crop((round(x*w/3),round(y*h/2),round((x+1)*w/3),round((y+1)*h/2)))
        # Discard isolated 1/255-alpha background residue; retain antialiased edges.
        cell.putalpha(cell.getchannel('A').point(lambda v:0 if v<=1 else v))
        box=cell.getchannel('A').getbbox()
        assert box,(stem,j,'blank source cell')
        assert cell.getchannel('A').histogram()[0]>cell.width*cell.height*.12,(stem,j,'not transparent')
        boxes.append(box);cells.append(cell)
    # Anticipation (hands by cheeks) precedes lying down in the nap motion.
    if stem=='13-nap':
        order=[0,1,2,4,3,5]
        cells=[cells[i] for i in order];boxes=[boxes[i] for i in order]
    maxw=max(b[2]-b[0] for b in boxes);maxh=max(b[3]-b[1] for b in boxes)
    scale=min(304/maxw,242/maxh)
    text_layer=label(item['caption'])
    save_png(text_layer,ROOT/'layers'/f'{stem}-text.png')
    frames=[];stats=[]
    for j,(cell,b) in enumerate(zip(cells,boxes)):
        crop=cell.crop(b)
        size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
        art=Image.new('RGBA',(360,360));small=crop.resize(size,Image.Resampling.LANCZOS)
        pos=(round((360-size[0])/2),334-size[1])
        art.alpha_composite(small,pos)
        save_png(art,ROOT/'layers'/stem/f'{j+1:02}.png')
        out=art.copy();out.alpha_composite(text_layer)
        save_png(out,ROOT/'frames'/stem/f'{j+1:02}.png')
        bb=out.getchannel('A').getbbox();margin=min(bb[0],bb[1],360-bb[2],360-bb[3])
        assert margin>=12,(stem,j,'insufficient safety margin',bb)
        frames.append(out);stats.append({'frame':j+1,'bbox':bb,'minimum_margin_px':margin,'source_bbox':b})
    target=ROOT/'webp'/f'{stem}.webp';target.parent.mkdir(exist_ok=True)
    frames[0].save(target,save_all=True,append_images=frames[1:],duration=item['durations_ms'],loop=4,
                   lossless=True,method=6,exact=True,background=(0,0,0,0),icc_profile=ICC,exif=EXIF)
    assert target.stat().st_size<=650000,(stem,'file exceeds 650,000 bytes')
    decoded=Image.open(target);assert decoded.n_frames==6 and decoded.info['loop']==4
    assert decoded.size==(360,360) and decoded.getexif()[282]==72 and decoded.getexif()[283]==72
    for i,frame in enumerate(frames):
        decoded.seek(i);got=decoded.convert('RGBA')
        assert ImageChops.difference(got.getchannel('A'),frame.getchannel('A')).getbbox() is None,(stem,i,'alpha mismatch')
        # RGB is immaterial where alpha is zero. Verify every visible channel exactly.
        mask=frame.getchannel('A').point(lambda v:255 if v else 0)
        for c in 'RGB':
            diff=ImageChops.multiply(ImageChops.difference(got.getchannel(c),frame.getchannel(c)),mask)
            assert diff.getbbox() is None,(stem,i,'visible RGB mismatch')
    save_png(frames[-1],ROOT/'thumbnails'/f'{stem}.png')
    info=riff_info(target)
    assert info['loop']==4 and info['durations_ms']==item['durations_ms']
    assert info['background_bgra']==[0,0,0,0]
    make_strip(stem,frames)
    return {'id':stem,'member':item['member'],'caption':item['caption'].replace('\n',' '),
            'size':[360,360],'frames':6,'loop':4,'durations_ms':item['durations_ms'],
            'cycle_ms':sum(item['durations_ms']),'bytes':target.stat().st_size,
            'dpi':[72,72],'profile':'sRGB + alpha','lossless_visible_pixel_match':True,
            'last_frame_is_thumbnail':True,'frame_stats':stats,'riff':info}

def make_strip(stem,frames):
    im=Image.new('RGB',(1080,400),'#f5f3ee');d=ImageDraw.Draw(im)
    f=ImageFont.truetype(FONT,14,index=FONT_INDEX)
    for row,bg in enumerate(['#ffffff','#30343b']):
        for col,frame in enumerate(frames):
            tile=Image.new('RGBA',(180,180),bg);tile.alpha_composite(frame.resize((180,180),Image.Resampling.LANCZOS))
            im.paste(tile.convert('RGB'),(col*180,row*200+20))
            d.text((col*180+8,row*200+2),f'F{col+1}',font=f,fill='#35291f')
    im.save(ROOT/'qa'/f'{stem}-frames.jpg',quality=95)

def overview(items):
    for bg,labelname in [('#ffffff','white'),('#30343b','dark')]:
        im=Image.new('RGB',(1200,880),bg);d=ImageDraw.Draw(im);f=ImageFont.truetype(FONT,16,index=FONT_INDEX)
        for i,item in enumerate(items):
            p=ROOT/'thumbnails'/f'{item["id"]}.png'
            if not p.exists():continue
            pic=Image.open(p).convert('RGBA').resize((180,180),Image.Resampling.LANCZOS)
            x=i%6*200+10;y=i//6*220+10
            im.paste(pic,(x,y),pic.getchannel('A'))
            d.text((x+8,y+187),f'{i+1:02} · {item["member"]}',font=f,fill='#6f655a' if labelname=='white' else '#dad5cc')
        im.save(ROOT/'qa'/f'overview-{labelname}.jpg',quality=96)

def preview(items):
    dataset=json.dumps([{**x,'caption':x['caption'].replace('\n',' ')} for x in items],ensure_ascii=False)
    page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>다시 합주할래? · 24종</title>
<style>*{box-sizing:border-box}body{margin:0;background:#eeeae3;color:#30291f;font-family:-apple-system,BlinkMacSystemFont,sans-serif}header{padding:36px 5vw 20px}h1{font-size:30px;margin:0 0 9px}p{line-height:1.7}nav{display:flex;flex-wrap:wrap;gap:9px;margin:20px 0}button,select{font:inherit;padding:10px 16px;border:1px solid #c9c0b4;border-radius:12px;background:#fff;cursor:pointer}main{padding:0 5vw 40px;display:grid;grid-template-columns:repeat(auto-fit,minmax(var(--card,205px),1fr));gap:16px}.card{border-radius:18px;overflow:hidden;background:#fff;border:1px solid #d9d2c7}.stage{background:var(--stage,#fff);display:flex;justify-content:center;align-items:center;min-height:210px}.stage img{max-width:100%;width:var(--size,180px);height:auto}.meta{padding:12px 16px}.meta strong{display:block}.meta small{color:#796e62}.meta a{font-size:12px;color:#635b9c;margin-right:10px}.missing{opacity:.25}footer{padding:16px 5vw 40px;color:#736c60}dialog{border:0;border-radius:20px;padding:25px;max-width:min(1100px,95vw)}dialog img{max-width:100%}</style>
<header><h1>다시 합주할래?</h1><p>어게이ㄴ식스 × 유닛5팀 · 7명의 말투로 만든 24종<br>360 × 360 · 6프레임 · 4회 재생 · 마지막 표정 800ms</p><nav><button onclick="setBg('#fff')">밝은 배경</button><button onclick="setBg('#30343b')">어두운 배경</button><button onclick="setSize(180)">180px</button><button onclick="setSize(360)">360px</button><button onclick="mode='webp';render()">움직임 재생</button><button onclick="mode='thumbnails';render()">마지막 표정</button><select id="member" onchange="render()"><option value="">모두 보기</option></select></nav></header><main id="grid"></main><footer>PNG 프레임은 frames/의 01–06 순서입니다. 시간표는 timing.csv / 프레임시간.json을 사용하세요.<br>캐릭터 디자인과 동작은 창작이며, 실제 외모를 재현하지 않았습니다.</footer><dialog id="dlg"><button onclick="dlg.close()">닫기</button><img id="strip"></dialog><script>const items=__DATA__;let mode='webp';for(const m of [...new Set(items.map(x=>x.member))])member.add(new Option(m,m));function setBg(c){document.documentElement.style.setProperty('--stage',c)}function setSize(n){document.documentElement.style.setProperty('--size',n+'px');document.documentElement.style.setProperty('--card',(n+32)+'px')}function showStrip(id){strip.src='qa/'+id+'-frames.jpg';dlg.showModal()}function render(){grid.innerHTML=items.filter(x=>!member.value||member.value===x.member).map(x=>{const ext=mode==='webp'?'webp':'png';return `<article class="card"><div class="stage"><img src="${mode}/${x.id}.${ext}?r=${Date.now()}" alt="${x.caption}"></div><div class="meta"><strong>${x.id.slice(0,2)} ${x.caption}</strong><p><small>${x.member} · 160/140/140/140/180/800ms</small></p><a href="webp/${x.id}.webp" download>WebP</a><a href="thumbnails/${x.id}.png" download>마지막 PNG</a><a href="#" onclick="showStrip('${x.id}');return false">프레임 보기</a></div></article>`}).join('')}render();</script></html>'''
    (ROOT/'index.html').write_text(page.replace('__DATA__',dataset))

def main():
    p=argparse.ArgumentParser();p.add_argument('--only',nargs='*');args=p.parse_args()
    items=DATA['items'];results={}
    previous=ROOT/'qa/validation.json'
    if previous.exists():results={r['id']:r for r in json.loads(previous.read_text())}
    for item in items:
        if args.only and item['id'] not in args.only:continue
        r=process(item)
        if r:results[r['id']]=r;print(item['id'],r['bytes'],'bytes, verified')
    previous.write_text(json.dumps(list(results.values()),ensure_ascii=False,indent=2))
    overview(items);preview(items)
    timings=[]
    for x in items:
        folder=ROOT/'frames'/x['id']
        if not folder.exists():continue
        with (folder/'timing.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(['filename','duration_ms'])
            for i,ms in enumerate(x['durations_ms'],1):
                writer.writerow([f'{i:02}.png',ms]);timings.append([x['id'],x['member'],f'{i:02}.png',ms,4])
    with (ROOT/'timing.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['emoticon','member','frame','duration_ms','loop']);writer.writerows(timings)
    (ROOT/'프레임시간.json').write_text(json.dumps({'loop':4,'items':[{k:x[k] for k in ['id','caption','member','durations_ms']} for x in items]},ensure_ascii=False,indent=2))
    print('Completed',len(results),'/ 24')

if __name__=='__main__':main()
