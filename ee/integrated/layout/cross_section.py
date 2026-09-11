"""Preliminary 2D quasi-static coated-microstrip model; not channel sign-off."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import argparse,json,time
from pathlib import Path
EPS0=8.8541878128e-12;C0=299792458

def cross_section(width,gap=None,step=.002,er=4.0,mask_er=3.6):
 h=.07366;t=.04064;mask=.0127
 centers=[0.] if gap is None else [-(width+gap)/2,(width+gap)/2]
 edges=[a for c in centers for a in [c-width/2,c+width/2]]
 xs=np.unique(np.round(np.r_[np.arange(-.45,.450001,step),edges,[-2.,-1.5,-1.1,-.8,-.6,-.5,.5,.6,.8,1.1,1.5,2.]],9))
 ys=np.unique(np.round(np.r_[np.arange(0,.180001,step),[h,h+t,h+mask,h+t+mask,.2,.23,.27,.32,.4,.5,.65,.85,1.1,1.5,2.]],9))
 xx,yy=np.meshgrid(xs,ys);ny,nx=xx.shape;n=nx*ny
 boundary=np.zeros_like(xx,dtype=bool);boundary[[0,-1],:]=True;boundary[:,[0,-1]]=True
 electrodes=[];fixed=boundary.copy();potential=np.zeros_like(xx)
 for k,c in enumerate(centers):
  m=(np.abs(xx-c)<=width/2+1e-8)&(yy>=h-1e-8)&(yy<=h+t+1e-8);electrodes.append(m);fixed|=m;potential[m]=1 if k==0 else -1
 free=~fixed;ids=np.full(n,-1,int);ids[free.ravel()]=np.arange(free.sum());ids=ids.reshape(ny,nx)
 dx=np.diff(xs);dy=np.diff(ys);wx=np.r_[dx[0]/2,(dx[:-1]+dx[1:])/2,dx[-1]/2];wy=np.r_[dy[0]/2,(dy[:-1]+dy[1:])/2,dy[-1]/2]
 def material(x,y,vacuum):
  if vacuum:return np.ones(np.broadcast_shapes(x.shape,y.shape))
  eps=np.where(y<h,er,1.)+np.zeros_like(x)
  coated=(y>=h)&(y<=h+mask)
  for c in centers:coated=coated|((np.abs(x-c)<=width/2+mask)&(y>=h)&(y<=h+t+mask))
  return np.where(coated,mask_er,eps)
 def solve(vacuum):
  # Finite-volume face conductances. Geometry dimensions cancel in 2D C/length.
  gx=material((xs[:-1]+xs[1:])[None,:]/2,ys[:,None],vacuum)*wy[:,None]/dx[None,:]
  gy=material(xs[None,:],(ys[:-1]+ys[1:])[:,None]/2,vacuum)*wx[None,:]/dy[:,None]
  rr=[];cc=[];vv=[];rhs=np.zeros(free.sum());diagonal=np.zeros(free.sum())
  pairs=[(ids[:,:-1],ids[:,1:],potential[:,:-1],potential[:,1:],gx),(ids[:-1,:],ids[1:,:],potential[:-1,:],potential[1:,:],gy)]
  for ia,ib,va,vb,g in pairs:
   for a,b,v,g in [(ia,ib,vb,g),(ib,ia,va,g)]:
    m=a>=0;np.add.at(diagonal,a[m],g[m]);both=m&(b>=0);rr.extend(a[both]);cc.extend(b[both]);vv.extend(-g[both]);bd=m&(b<0);np.add.at(rhs,a[bd],g[bd]*v[bd])
  rr.extend(np.arange(len(rhs)));cc.extend(np.arange(len(rhs)));vv.extend(diagonal)
  A=coo_matrix((vv,(rr,cc)),shape=(len(rhs),len(rhs))).tocsr();v=potential.copy();v[free]=spsolve(A,rhs)
  charge=0.;m=electrodes[0]
  for ma,mb,va,vb,g in [(m[:,:-1],m[:,1:],v[:,:-1],v[:,1:],gx),(m[:-1,:],m[1:,:],v[:-1,:],v[1:,:],gy)]:
   hit=ma&~mb;charge+=np.sum(g[hit]*(va[hit]-vb[hit]));hit=mb&~ma;charge+=np.sum(g[hit]*(vb[hit]-va[hit]))
  return charge*EPS0
 capacitance=solve(False);vac=solve(True);z=1/(C0*np.sqrt(capacitance*vac));velocity=C0*np.sqrt(vac/capacitance)
 return {'width_mm':width,'gap_mm':gap,'mesh_step_mm':step,'substrate_er':er,'mask_er':mask_er,'Z0_ohm':float(z),'Zdiff_ohm':float(2*z) if gap is not None else None,'delay_ps_per_mm':float(1e9/velocity),'nodes':n}
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=Path(__file__).with_name('cross-section-estimates.json'));args=parser.parse_args()
 cases=[(.0762,None),(.1143,None),(.11,None),(.127,.127),(.12,.15),(.1,.2)]
 results=[]
 for w,g in cases:
  start=time.monotonic();r=cross_section(w,g);print(r,round(time.monotonic()-start,1),flush=True);results.append(r)
 args.output.open('w').write(json.dumps({'method':'2D finite-volume electrostatic C and C_vacuum; ideal infinite copper conductivity; conformal mask approximation; no neighboring pads, traces, vias or glass weave','signoff':False,'results':results},indent=2)+'\n')
