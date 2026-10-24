import json,struct,sys
from pathlib import Path
import numpy as np
from align_reference import readwav

source,rendered,output=sys.argv[1:4]
sr,x=readwav(source);sr2,y=readwav(rendered);assert sr==sr2
hop=480

def envelope(a):
 a=a[:len(a)//hop*hop].reshape(-1,hop,2)
 return np.sqrt(np.mean(a*a,axis=(1,2))).astype(float)

def best_lag(a,b,start,end):
 i,j=round(start*sr/hop),round(end*sr/hop)
 # The waveform changes pitch; broadband attack envelopes remain comparable.
 scores=[]
 for lag in range(-30,31):
  begin=max(i,-lag,0);finish=min(j,len(a),len(b)-lag)
  aa=a[begin:finish];bb=b[begin+lag:finish+lag]
  scores.append(float(np.corrcoef(aa,bb)[0,1]))
 n=int(np.argmax(scores));return n-30,scores[n]

ex,ey=envelope(x),envelope(y)
checks=[{'range_seconds':[a,b],'lag_bins':v[0],'correlation':v[1]} for a,b in [(0.3,9),(45,65),(110,130),(168,184)] for v in [best_lag(ex,ey,a,b)]]
lag=round(float(np.median([v['lag_bins'] for v in checks])))
shift=lag*hop
if shift>=0:z=y[shift:shift+len(x)].copy()
else:z=np.concatenate((np.zeros((-shift,2),dtype=np.float32),y))[:len(x)]
if len(z)<len(x):z=np.pad(z,((0,len(x)-len(z)),(0,0)))
# Avoid clipping while keeping the source's dynamics.
peak=float(np.max(np.abs(z)));gain=min(1.0,0.98/max(peak,1e-9));z*=gain
assert len(z)==len(x) and np.all(np.isfinite(z))
body=z.astype('<f4').tobytes();fmt=struct.pack('<HHIIHH',3,2,sr,sr*8,8,32)
Path(output).write_bytes(b'RIFF'+struct.pack('<I',36+len(body))+b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(body))+body)
# Check the spectral shift on several sustained sections, independent of metadata.
n=65536;frequencies=np.fft.rfftfreq(n,1/sr);grid=np.geomspace(160,6000,2000)
window=np.hanning(n)
measured=[]
for start in [2,5,17,48,114,172]:
 k=round(start*sr)
 sx=np.abs(np.fft.rfft(x[k:k+n].mean(axis=1)*window))
 sy=np.abs(np.fft.rfft(z[k:k+n].mean(axis=1)*window))
 target=np.log1p(np.interp(grid,frequencies,sy))
 candidates=np.arange(-6.,-3.99,.025)
 scores=[]
 for semi in candidates:
  reference=np.log1p(np.interp(grid/(2**(semi/12)),frequencies,sx))
  scores.append(float(np.corrcoef(reference,target)[0,1]))
 best=int(np.argmax(scores));measured.append({'start_seconds':start,'semitones':round(float(candidates[best]),3),'correlation':scores[best]})
report={'requested_shift_semitones':-5,'rate':1.0,'sample_rate':sr,'channels':2,'frames':len(z),'duration_seconds':len(z)/sr,'raw_envelope_checks':checks,'trimmed_delay_seconds':shift/sr,'applied_gain':gain,'peak':float(np.max(np.abs(z))),'spectral_checks':measured,'median_measured_shift_semitones':float(np.median([v['semitones'] for v in measured])),'post_trim_envelope_checks':[{'range_seconds':[a,b],'lag_ms':v[0]*10,'correlation':v[1]} for a,b in [(0.3,9),(45,65),(110,130),(168,184)] for v in [best_lag(ex,envelope(z),a,b)]]}
Path(output).with_suffix('.qa.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
