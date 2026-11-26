"""Figures for the manuscript. Every plotted number is a result recorded in README.md / results/.
python3 make_figures.py   -> figures/fig*.png (600 dpi), .tiff (1200 dpi line art), .pdf (vector)"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
B,O,A='#257de0','#f47230','#00b894'; INK='#191919'; SEC='#666666'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.edgecolor':SEC,'axes.linewidth':0.6,'axes.labelcolor':INK,'xtick.color':SEC,'ytick.color':SEC,
                     'axes.spines.top':False,'axes.spines.right':False,'grid.color':'#e3e3e3','grid.linewidth':0.5,'legend.frameon':False,'lines.linewidth':1.6,'lines.markersize':5})
def save(fig,name):
    fig.savefig('figures/%s.pdf'%name,bbox_inches='tight'); fig.savefig('figures/%s.png'%name,dpi=600,bbox_inches='tight'); fig.savefig('figures/%s.tiff'%name,dpi=1200,bbox_inches='tight',pil_kwargs={'compression':'tiff_lzw'}); plt.close(fig)
# ---------------- Fig. 2: minimum trail weight versus rounds
fig,ax=plt.subplots(1,2,figsize=(7.0,2.7),sharey=True)
a=ax[0]; a.set_title('(a) Related-key differential',fontsize=8,loc='left',color=INK)
a.plot([6,7,8,9],[2,4,8,11],color=B,marker='o',label='Simon 32/64 (all keys)')
a.plot([6,7,8,9],[2,6,11,19],color=O,marker='s',label='Proposed, all keys (data + key)')
a.plot([6,7,8,9],[2,4,6,8],color=A,marker='^',ls='--',label='Proposed, weak keys (data only)')
for r,v in((10,21),(11,24)):
    a.annotate('',xy=(r,v-2.6),xytext=(r,v),arrowprops=dict(arrowstyle='->',color=B,lw=1.2)); a.plot([r],[v],color=B,marker='_',ms=9,mew=1.6)
for r,v in((10,22),(11,25)):
    a.annotate('',xy=(r,v+2.6),xytext=(r,v),arrowprops=dict(arrowstyle='->',color=O,lw=1.2)); a.plot([r],[v],color=O,marker='_',ms=9,mew=1.6)
a.annotate('Proposed: lower bounds\nSimon: trails found',xy=(10.5,13),xytext=(9.55,13.5),color=INK,fontsize=7,va='center')
b=ax[1]; b.set_title('(b) Rotational-XOR, rotation 1',fontsize=8,loc='left',color=INK)
b.plot([5,6,7,8,9],[0,0,4,6,10],color=B,marker='o'); b.plot([9,10,11],[10,14,24],color=B,marker='o',mfc='white',ls=':')
b.plot([5,6,7,8,9,10],[0,0,4,8,14,22],color=O,marker='s')
b.plot([7,8,9,10],[4,6,8,11],color=A,marker='^',ls='--')
b.plot([11,11],[25,29],color=O,lw=1.6); b.plot([11,11],[25,29],color=O,marker='_',ms=9,mew=1.6,ls='')
b.annotate('Proposed: between\n25 and 29',xy=(11,27),xytext=(9.0,28.3),color=INK,fontsize=7,va='center')
b.annotate('published values\n(Lu et al.)',xy=(10.5,19),xytext=(10.62,15.2),color=INK,fontsize=7,va='center')
for x in ax: x.set_xlabel('Rounds'); x.grid(axis='y'); x.set_xticks(range(5,12)); x.set_ylim(-1,31)
ax[0].set_ylabel('Minimum trail weight  ($-\\log_2$ probability)'); ax[0].set_xlim(5.6,11.4); ax[1].set_xlim(4.6,11.4)
ax[0].legend(loc='upper left',fontsize=7,handlelength=2.6,bbox_to_anchor=(0.0,1.0))
save(fig,'fig2_trail_weights')
# ---------------- Fig. 3: weak-key trade-off of v3, predicted versus measured class density
fig,ax=plt.subplots(1,2,figsize=(7.0,2.6))
a=ax[0]; a.set_title('(a) Related-key, 8 rounds',fontsize=8,loc='left',color=INK)
a.plot([6,7,8],[21,15,10],color=O,marker='s',label='Proposed: minimum key weight'); a.plot([9],[2],color=O,marker='s'); a.plot([8,9],[10,2],color=O,ls=':')
a.axvline(8,color=B,lw=1.2,ls='--'); a.annotate('Simon 32/64:\ndata weight 8\nfor every key',xy=(8,17),xytext=(8.12,17.5),color=INK,fontsize=7,va='center')
for x,y in((6,21),(7,15),(8,10),(9,2)): a.annotate(str(y),xy=(x,y),xytext=(-9,-9),textcoords='offset points',color=INK,fontsize=7)
a.set_xlabel('Data-path weight of the trail'); a.set_ylabel('Key weight  ($-\\log_2$ class density)'); a.set_xticks([6,7,8,9]); a.set_xlim(5.6,9.9); a.set_ylim(0,24); a.grid(axis='y')
b=ax[1]; b.set_title('(b) Weak-key classes: predicted and measured',fontsize=8,loc='left',color=INK)
pred=[21,15,10,17,24]; meas=[20.93,14.99,10.00,17.01,20.94]
b.plot([8,25],[8,25],color=SEC,lw=0.8,ls='--'); b.plot(pred,meas,color=O,marker='s',ls='',ms=6)
for p,m,l,o in zip(pred,meas,['RK, 8 r','RK, 8 r','RK, 8 r','RX, 9 r','RK, 9 r'],[(-52,6),(6,-9),(6,-9),(6,-9),(-18,-13)]): b.annotate('%s: %.2f'%(l,m),xy=(p,m),xytext=o,textcoords='offset points',color=INK,fontsize=7)
b.set_xlabel('Predicted key weight (SAT model)'); b.set_ylabel('Measured  $-\\log_2$ density'); b.set_xlim(8,26.5); b.set_ylim(8,23.5); b.set_xticks(range(8,27,2)); b.set_yticks(range(8,24,2)); b.grid(True)
save(fig,'fig3_weak_key')
# ---------------- Fig. 1: one key-schedule step, Simon 32/64 and v3
def box(a,x,y,t,w=1.25,h=0.5,fc='white',ec=INK):
    a.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=0.02,rounding_size=0.06',fc=fc,ec=ec,lw=0.8)); a.text(x,y,t,ha='center',va='center',fontsize=7,color=INK)
def xor(a,x,y): a.add_patch(Circle((x,y),0.13,fc='white',ec=INK,lw=0.8)); a.plot([x-0.13,x+0.13],[y,y],color=INK,lw=0.8); a.plot([x,x],[y-0.13,y+0.13],color=INK,lw=0.8)
def arr(a,p,q,c=INK,ls='-'): a.add_patch(FancyArrowPatch(p,q,arrowstyle='-|>',mutation_scale=7,color=c,lw=0.8,ls=ls,shrinkA=0,shrinkB=0))
fig,ax=plt.subplots(1,2,figsize=(7.0,3.0))
L=lambda a,xs,ys,c=INK: a.plot(xs,ys,color=c,lw=0.8,solid_capstyle='round')
for a,v3,title in((ax[0],False,'(a) Simon 32/64'),(ax[1],True,'(b) Proposed schedule')):
    a.set_xlim(-0.2,7.2); a.set_ylim(-0.5,4.6); a.axis('off'); a.set_title(title,fontsize=8,loc='left',color=INK)
    for x,t in zip([0.7,2.5,4.3,6.1],['$k_{i-4}$','$k_{i-3}$','$k_{i-2}$','$k_{i-1}$']): box(a,x,4.1,t)
    box(a,6.1,3.15,'$\\ggg 3$',w=0.9); arr(a,(6.1,3.85),(6.1,3.4)); L(a,[6.1,6.1],[2.9,2.4]); arr(a,(6.1,2.4),(2.63,2.4))
    xor(a,2.5,2.4); arr(a,(2.5,3.85),(2.5,2.53))
    if v3:
        box(a,4.3,3.15,'$S^1(\\cdot)\\wedge S^8(\\cdot)$',w=1.75,fc='#fde3d5',ec=O)
        L(a,[5.475,5.3],[4.1,4.1],O); arr(a,(5.3,4.1),(4.9,3.42),c=O); L(a,[4.3,4.3],[2.9,2.75],O); arr(a,(4.3,2.75),(2.6,2.47),c=O)
    a.text(2.28,2.02,'$t$',fontsize=7,color=INK,ha='right')
    L(a,[2.5,2.5],[2.27,1.9]); arr(a,(2.5,1.9),(2.5,1.43)); L(a,[2.5,3.3],[1.9,1.9]); arr(a,(3.3,1.9),(3.55,1.9)); box(a,4.0,1.9,'$\\ggg 1$',w=0.9)
    L(a,[4.45,4.9,4.9],[1.9,1.9,1.3]); arr(a,(4.9,1.3),(2.63,1.3)); xor(a,2.5,1.3)
    arr(a,(2.5,1.17),(2.5,0.73)); xor(a,2.5,0.6); L(a,[0.7,0.7],[3.85,0.6]); arr(a,(0.7,0.6),(2.37,0.6))
    a.text(3.55,0.6,'$c_i$',fontsize=7,color=INK,va='center'); arr(a,(3.4,0.6),(2.63,0.6))
    arr(a,(2.5,0.47),(2.5,0.02)); a.text(2.5,-0.25,'$k_i$',ha='center',fontsize=7,color=INK)
save(fig,'fig1_schedule')
print('figures written')
