import json,struct
from pathlib import Path
import numpy as np

def readwav(path):
 p=Path(path).read_bytes(); at=12
 while at+8<len(p):
  tag=p[at:at+4];sz=struct.unpack_from('<I',p,at+4)[0]
  if tag==b'fmt ': fmt,ch,rate,_,_,bits=struct.unpack_from('<HHIIHH',p,at+8)
  if tag==b'data': return rate,np.frombuffer(p,dtype='<f4',count=sz//4,offset=at+8).reshape(-1,ch)
  at+=8+sz+(sz%2)
 raise ValueError('no data')

def corr(x,y):
 n=1<<(len(x)+len(y)-2).bit_length()
 cc=np.fft.irfft(np.fft.rfft(x,n)*np.fft.rfft(y[::-1],n),n)[len(y)-1:len(x)]
 en=np.concatenate(([0.],np.cumsum(x*x)))
 denom=np.sqrt(np.maximum(en[len(y):]-en[:-len(y)],1e-20)*np.sum(y*y))
 return cc/denom

if __name__=='__main__':
 r,x=readwav('audio/reference/instrumental_resampled.wav'); s,y=readwav('audio/reference/apple_official_preview.wav'); assert r==s
 print('Lengths',len(x)/r,len(y)/r,'rate',r)
 # Stereo side channel substantially suppresses the center-panned lead vocal.
 xd=(x[:,0]-x[:,1])[::22].astype(float); yd=(y[:,0]-y[:,1])[::22].astype(float)
 results=[]
 for start in [5,15,25,35,45,55,65,75]:
  if start+8>len(y)/r:continue
  ya=yd[round(start*r/22):round((start+8)*r/22)]
  c=corr(xd,ya);i=int(np.argmax(c));t=i*22/r;coef=float(c[i])
  print('preview',start,'instrumental',round(t,5),'offset',round(t-start,5),'correlation',round(coef,5))
  results.append({'preview':start,'instrumental':t,'offset':t-start,'correlation':coef})
 Path('audio/reference/alignment.json').write_text(json.dumps(results,indent=2))
