import numpy as np
from numpy import pi,sin,cos,sqrt,exp
from scipy.integrate import quad,solve_ivp
from scipy.optimize import brentq,minimize_scalar

def integ(f,a,b):return quad(f,a,b,epsabs=1e-9,epsrel=2e-10,limit=200)[0]
def half(Vm,R,L,E=0,w=2*pi*60,alpha=None):
 a=np.arcsin(E/Vm) if alpha is None else alpha
 if R and L:
  Z=np.hypot(R,w*L); ph=np.arctan2(w*L,R);q=w*L/R;A=Vm/Z;B=E/R;K=B-A*sin(a-ph)
  f=lambda x:A*sin(x-ph)-B+K*exp(-(x-a)/q)
 elif L:
  Z=w*L;ph=pi/2;q=float('inf');A=Vm/Z;B=E/Z;K=0
  f=lambda x:(Vm*(cos(a)-cos(x))-E*(x-a))/(w*L)
 else:
  Z=R;ph=0;q=0;A=Vm/R;B=E/R;K=0;f=lambda x:(Vm*sin(x)-E)/R
 grid=np.linspace(a+1e-7,a+2*pi,4000);b=None
 for x,y in zip(grid[:-1],grid[1:]):
  if f(x)>0 and f(y)<=0:b=brentq(f,x,y,xtol=1e-13);break
 if b is None:raise ValueError(('No zero',Vm,R,L,E,a))
 io=integ(f,a,b)/(2*pi);ir=sqrt(integ(lambda x:f(x)**2,a,b)/(2*pi));pr=R*ir**2;pe=E*io;ps=integ(lambda x:Vm*sin(x)*f(x),a,b)/(2*pi)
 return dict(Vm=Vm,R=R,L=L,E=E,w=w,a=a,b=b,Z=Z,ph=ph,q=q,A=A,B=B,K=K,io=io,ir=ir,pr=pr,pe=pe,ps=ps,pf=ps/(Vm/sqrt(2)*ir),f=f)

def full(Vm,R,L,E=0,w=2*pi*60):
 Z=np.hypot(R,w*L);ph=np.arctan2(w*L,R);q=w*L/R;A=Vm/Z;B=E/R
 k=exp(-pi/q);init=A*sin(ph)*(1+k)/(1-k)-B;K=init+A*sin(ph)+B
 f=lambda x:A*sin(x-ph)-B+K*exp(-x/q)
 opt=minimize_scalar(f,bounds=(0,pi),method='bounded');low=min(f(0),f(pi),opt.fun)
 if low< -1e-7:
  h=half(Vm,R,L,E,w);a=h['a'];b=h['b'];f=h['f'];mode='DCM'
  if b>pi+a:raise ValueError('unexpected')
 else:a=0;b=pi;mode='CCM'
 io=integ(f,a,b)/pi;ir=sqrt(integ(lambda x:f(x)**2,a,b)/pi);ps=integ(lambda x:Vm*sin(x)*f(x),a,b)/pi
 xx=np.linspace(a,b,10001);yy=f(xx);imin=0 if mode=='DCM' else min(yy);imax=max(yy)
 return dict(Vm=Vm,R=R,L=L,E=E,w=w,a=a,b=b,Z=Z,ph=ph,q=q,A=A,B=B,K=K,init=init,mode=mode,io=io,ir=ir,pr=R*ir**2,pe=E*io,ps=ps,pf=ps/(Vm/sqrt(2)*ir),imin=imin,imax=imax,ripple=imax-imin,I2=4*Vm/(3*pi*np.hypot(R,2*w*L)),f=f)

def freewheel(Vm,R,L,E=0,w=2*pi*60):
 q=w*L/R;Z=np.hypot(R,w*L);ph=np.arctan2(w*L,R);A=Vm/Z;B=E/R;k=exp(-pi/q)
 init=A*sin(ph)*k/(1-k)-B;K=init+A*sin(ph)+B
 f1=lambda x:A*sin(x-ph)-B+K*exp(-x/q)
 ip=f1(pi);f2=lambda x:(ip+B)*exp(-(x-pi)/q)-B
 f=lambda x:np.where(x<=pi,f1(x),f2(x))
 io=(integ(f1,0,pi)+integ(f2,pi,2*pi))/(2*pi)
 ir=sqrt((integ(lambda x:f1(x)**2,0,pi)+integ(lambda x:f2(x)**2,pi,2*pi))/(2*pi))
 isr=sqrt(integ(lambda x:f1(x)**2,0,pi)/(2*pi));ps=integ(lambda x:Vm*sin(x)*f1(x),0,pi)/(2*pi)
 xx=np.linspace(0,2*pi,12001);yy=f(xx)
 return dict(Vm=Vm,R=R,L=L,E=E,w=w,io=io,ir=ir,pr=R*ir**2,pe=E*io,ps=ps,pf=ps/(Vm/sqrt(2)*isr),imin=min(yy),imax=max(yy),ripple=np.ptp(yy),f=f)

def cap(Vm,R,C,w=2*pi*60,p=2*pi):
 q=w*R*C;off=pi-np.arctan(q)
 a=brentq(lambda x:sin(off)*exp(-(p+x-off)/q)-sin(x),0,pi/2,xtol=1e-14)
 vd=lambda x:Vm*sin(x)
 vf=lambda x:Vm*sin(off)*exp(-(x-off)/q)
 avg=(integ(vd,a,off)+integ(vf,off,p+a))/p
 ir=avg/R;idfun=lambda x:Vm/R*sin(x)+w*C*Vm*cos(x)
 res=minimize_scalar(lambda x:-idfun(x),bounds=(a,off),method='bounded');ip=max(idfun(a),-res.fun)
 return dict(a=a,off=off,vo=avg,ripple=Vm*(1-sin(a)),approx=Vm*p/q,ip=ip,io=ir,idavg=ir if p==2*pi else ir/2,q=q,Vm=Vm,R=R,C=C)

def lc(Vm,R,L,w=2*pi*60,rs=0):
 # Large-C ideal output, solve periodic current under abs(sin) with series resistance.
 if rs==0:
  def evalvo(V):
   a=np.arcsin(V/Vm)
   f=lambda x:(Vm*(cos(a)-cos(x))-V*(x-a))/(w*L)
   xs=np.linspace(pi/2+1e-7,pi+a,2000)
   roots=[(x,y) for x,y in zip(xs[:-1],xs[1:]) if f(x)*f(y)<=0]
   if not roots:return None
   b=brentq(f,*roots[0]);return integ(f,a,b)/pi-V/R,a,b,f
  vbase=2*Vm/pi
  ev=evalvo(vbase)
  if ev and ev[0]>=0:
   v=brentq(lambda v:evalvo(v)[0],vbase,Vm*(1-1e-9));_,a,b,f=evalvo(v);return dict(vo=v,io=v/R,mode='DCM',a=a,b=b)
  return dict(vo=vbase,io=vbase/R,mode='CCM',a=0,b=pi)
 # event ODE (finite series loss) robust integration across periods
 def current_for(V):
  t=np.linspace(0,pi,16001);i=0.;arr=[];h=t[1]
  for _ in range(50):
   prev=i;arr=[]
   for x in t[:-1]:
    s=Vm*sin(x+h/2)-V
    i=max(0,i*exp(-rs*h/(w*L))+s/rs*(1-exp(-rs*h/(w*L))));arr.append(i)
   if abs(i-prev)<1e-9:break
  return np.mean(arr),min(arr)
 v=brentq(lambda v:current_for(v)[0]-v/R,.1,Vm*.99999)
 io,imin=current_for(v);return dict(vo=v,io=io,mode='CCM' if imin>1e-5 else 'DCM')

def three(Vll,R,L=0,w=2*pi*60):
 Vm=sqrt(2)*Vll;v0=3*Vm/pi
 if L==0:ir=Vm/R*sqrt(.5+3*sqrt(3)/(4*pi))
 else:
  ns=np.arange(6,6001,6);amps=6*Vm/(pi*(ns**2-1))/np.hypot(R,ns*w*L);ir=sqrt((v0/R)**2+np.sum(amps**2)/2)
 io=v0/R;isr=sqrt(2/3)*ir;S=sqrt(3)*Vll*isr;P=R*ir**2
 return dict(Vll=Vll,Vm=Vm,vo=v0,io=io,ir=ir,idavg=io/3,idrms=ir/sqrt(3),isr=isr,S=S,P=P,pf=P/S,I6=6*Vm/(35*pi*np.hypot(R,6*w*L)))
