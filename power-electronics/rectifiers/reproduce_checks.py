"""Recompute independent numeric checks. Python 3.10+, NumPy, SciPy.
Run from this folder: python reproduce_checks.py
This verifies specified mathematical models, not proprietary PSpice libraries.
"""
from pathlib import Path
import json
from pe import *
data=json.loads((Path(__file__).parent/'results.json').read_text())
checks=[]
def check(name,error,tol):
 checks.append(dict(name=name,error=float(error),tolerance=tol,passed=bool(error<tol)))
for name,d in data.items():
 if not isinstance(d,dict):continue
 if all(k in d for k in ['a','b','L','R','E','Vm','w','io','pr','pe','ps']):
  check(name+' power balance',abs(d['ps']-d['pr']-d['pe'])/max(1,d['ps']),1e-8)
  if d['L']>0 and 'init' not in d and 'ph' in d:
   h=half(d['Vm'],d['R'],d['L'],d['E'],d['w'])
   sol=solve_ivp(lambda x,y:[(d['Vm']*sin(x)-d['R']*y[0]-d['E'])/(d['w']*d['L'])],(d['a'],d['b']),[0],rtol=1e-10,atol=1e-11,dense_output=True)
   x=np.linspace(d['a'],d['b'],801)
   check(name+' independent ODE',max(abs(sol.sol(x)[0]-h['f'](x))),2e-6)
 if 'q' in d and 'off' in d:
  period=pi if name.startswith(('E4','P4')) and not name.endswith('half') else 2*pi
  omega=377 if name.startswith(('P3-17','P3-18')) else 2*pi*60
  qdiode=integ(lambda x:d['Vm']/d['R']*sin(x)+omega*d['C']*d['Vm']*cos(x),d['a'],d['off'])/omega
  qload=d['io']*period/omega
  check(name+' capacitor charge balance',abs(qdiode-qload)/max(1,qdiode),1e-8)
n=np.arange(1,20001);A=40*np.sin(n*pi*.4)/(n*pi)
power=2*(4**2+sum(A*A/(2**2+(2*pi*50*n*.01)**2))/2)
check('E2-12 Fourier vs time',abs(power-data['E2-12']['P']),1e-7)
check('P4-51 ripple <=1.5A',data['design4-51']['ripple'],1.5)
check('P3-16 ripple <=1A',data['P3-16']['ripple'],1)
sol=solve_ivp(lambda t,y:[(y[1]-y[0]/100)/1e-4,(100-y[0])/1e-4],(0,.003),[100,0],rtol=1e-10,atol=1e-11,dense_output=True)
t=np.linspace(0,.003,3001);wd=sqrt(1e8-2500)
exact=100-10000/wd*exp(-50*t)*sin(wd*t)
check('HW1-2 exact vs state ODE',max(abs(exact-sol.sol(t)[0])),1e-6)
print(f'{sum(c["passed"] for c in checks)}/{len(checks)} checks passed')
for c in checks:
 if not c['passed']:print(c)
assert all(c['passed'] for c in checks)
