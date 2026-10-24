from pathlib import Path
import csv,json,zipfile,hashlib
from io import BytesIO
from PIL import Image,ImageChops,ImageCms
from build import ROOT,save_png,ICC

def icon():
    src=Image.open(ROOT/'source-sheets/tab-icon.png').convert('RGBA')
    src.putalpha(src.getchannel('A').point(lambda v:0 if v<=1 else v))
    crop=src.crop(src.getchannel('A').getbbox())
    scale=min(70/crop.width,70/crop.height)
    small=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(78,78));out.alpha_composite(small,((78-small.width)//2,(78-small.height)//2))
    path=ROOT/'icon/tab-78.png';save_png(out,path)
    assert path.stat().st_size<=16000
    im=Image.open(path);assert im.mode=='RGBA' and im.size==(78,78)
    bb=im.getchannel('A').getbbox();assert min(bb[0],bb[1],78-bb[2],78-bb[3])>=3
    info={'bytes':path.stat().st_size,'size':[78,78],'mode':im.mode,'dpi':im.info['dpi'],'bbox':bb,'transparent':True}
    (ROOT/'qa/icon-validation.json').write_text(json.dumps(info,indent=2))
    # View at actual 78px, and an enlarged pixel view on both backgrounds.
    board=Image.new('RGBA',(480,180),'white')
    for i,color in enumerate(['#ffffff','#30343b']):
        tile=Image.new('RGBA',(240,180),color);tile.alpha_composite(out,(12,50))
        tile.alpha_composite(out.resize((140,140),Image.Resampling.NEAREST),(96,20));board.alpha_composite(tile,(i*240,0))
    board.convert('RGB').save(ROOT/'qa/tab-icon-check.png')
    return info

def validate_and_report(icon_info):
    rows=sorted(json.loads((ROOT/'qa/validation.json').read_text()),key=lambda x:x['id'])
    assert len(rows)==24
    assert len(list((ROOT/'webp').glob('*.webp')))==24
    assert len(list((ROOT/'frames').glob('*/*.png')))==144
    minmargin=360
    for r in rows:
        for i in range(1,7):
            path=ROOT/'frames'/r['id']/f'{i:02}.png'
            im=Image.open(path);assert im.size==(360,360) and im.mode=='RGBA'
            assert all(abs(v-72)<.02 for v in im.info['dpi'])
            profile=ImageCms.ImageCmsProfile(BytesIO(im.info['icc_profile']))
            assert profile.profile.xcolor_space.strip()=='RGB'
            assert 'srgb' in ImageCms.getProfileDescription(profile).lower()
            assert im.getchannel('A').getextrema()[0]==0
            bb=im.getchannel('A').getbbox();margin=min(bb[0],bb[1],360-bb[2],360-bb[3]);minmargin=min(minmargin,margin)
            assert margin>=12
        last=Image.open(ROOT/'frames'/r['id']/'06.png').convert('RGBA')
        thumb=Image.open(ROOT/'thumbnails'/f'{r["id"]}.png').convert('RGBA')
        assert ImageChops.difference(last,thumb).getbbox(alpha_only=False) is None
        assert r['bytes']<=650000 and r['loop']==4 and r['frames']<=24
        assert r['durations_ms']==[160,140,140,140,180,800]
        assert r['lossless_visible_pixel_match']
    with (ROOT/'검사값.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['파일','멤버','문구','폭','높이','프레임','반복','1회_ms','파일_bytes','최소여백_px'])
        for r in rows:w.writerow([r['id']+'.webp',r['member'],r['caption'],360,360,6,4,1560,r['bytes'],min(x['minimum_margin_px'] for x in r['frame_stats'])])
    md=f'''# 최종 검수 결과

24종 WebP와 PNG 프레임 144장을 파일에서 다시 읽어 검사했습니다.

| 항목 | 결과 |
|---|---|
| 종수 | 24종 |
| 크기 | 모두 360×360px |
| 색상·투명도 | sRGB + 알파, 모든 프레임에 완전 투명 영역 존재 |
| 해상도 | PNG 72dpi 설정, WebP EXIF 72dpi |
| 프레임 | 각 6프레임, 총 144 PNG |
| 재생 | ANIM Loop Count=4 |
| 프레임 시간 | 160 / 140 / 140 / 140 / 180 / 800ms |
| 총 시간 | 1회 1.56초, 4회 6.24초 |
| WebP 용량 | {min(r['bytes'] for r in rows):,}~{max(r['bytes'] for r in rows):,}바이트, 모두 650,000바이트 이하 |
| 가장자리 여백 | 모든 PNG 프레임 최소 {minmargin}px |
| PNG↔WebP | 144개 프레임의 알파와 보이는 RGB 픽셀 일치 |
| 마지막 프레임 | 24종 모두 06.png와 썸네일의 픽셀 일치 |
| 문구 | 동작별 고정 레이어, 흰색 외곽선 4px |
| 탭 아이콘 | 78×78px 투명 RGBA PNG, {icon_info['bytes']:,}바이트, 16,000바이트 이하 |

용량 제한은 650KB를 650,000바이트, 16KB를 16,000바이트로 잡아 더 작은 한도로 검사했습니다. 최종 파일은 투명 무손실 WebP입니다.

## 화면 확인

밝은 배경·어두운 배경의 마지막 표정 모음은 `qa/overview-white.jpg`, `qa/overview-dark.jpg`입니다. 각 동작의 `qa/*-frames.jpg`에는 180px 크기에서 F1~F6을 두 배경으로 비교한 그림이 있습니다.

원화 검사 과정에서 05번 중복 피크, 08번 중복 꼬리, 12번 마이크를 든 손과 꼬리 방향, 15번 악기 건반을 수정했습니다. 13번은 잠드는 흐름에 맞게 원화 순서를 1·2·3·5·4·6으로 조정했습니다. 개별 프레임은 포즈별 원화이므로 굴곡과 윤곽이 조금씩 달라지는 손그림 방식입니다.

파일 규격 검증은 카카오의 상품 심사나 게시 승인을 의미하지 않습니다. 실제 제출은 수행하지 않았습니다.
'''
    (ROOT/'검수결과.md').write_text(md)
    final={'passed':True,'emoticons':24,'frames':144,'min_margin_px':minmargin,'max_webp_bytes':max(r['bytes'] for r in rows),'min_webp_bytes':min(r['bytes'] for r in rows),'icon':icon_info}
    (ROOT/'qa/final-validation.json').write_text(json.dumps(final,ensure_ascii=False,indent=2))
    return final

def package():
    common=['읽어주세요.md','검수결과.md','검사값.csv','timing.csv','프레임시간.json','qa/validation.json','qa/final-validation.json','qa/icon-validation.json','qa/browser-validation.json']
    usage=common+['index.html']
    for folder in ['webp','icon','thumbnails']:
        usage += [str(p.relative_to(ROOT)) for p in sorted((ROOT/folder).glob('*')) if p.is_file()]
    usage += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'qa').glob('*.jpg'))]
    usage += ['qa/tab-icon-check.png']
    originals=common+['prompts.json','prompts-addendum.json','generation-record.json','scripts/build.py','scripts/package.py']
    for folder in ['frames','layers']:
        originals += [str(p.relative_to(ROOT)) for p in sorted((ROOT/folder).rglob('*')) if p.is_file()]
    originals += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'source-sheets').glob('*.png'))]
    out=[]
    for label,files in [('최종파일',usage),('PNG프레임-편집원본',originals)]:
        target=ROOT/f'다시-합주할래-24종-{label}.zip'
        files=sorted(set(files))
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for rel in files:z.write(ROOT/rel,rel)
        with zipfile.ZipFile(target) as z:
            assert z.testzip() is None
            assert len(z.namelist())==len(files)
            if label=='최종파일':assert sum(x.startswith('webp/') for x in z.namelist())==24
            else:assert sum(x.startswith('frames/') and x.endswith('.png') for x in z.namelist())==144
        out.append({'file':target.name,'bytes':target.stat().st_size,'files':len(files),'crc_ok':True,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    (ROOT/'qa/package-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    return out

if __name__=='__main__':
    i=icon();v=validate_and_report(i);packs=package();print(json.dumps({'validation':v,'packages':packs},ensure_ascii=False))
