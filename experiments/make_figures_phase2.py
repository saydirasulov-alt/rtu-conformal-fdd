"""Manuscript figures 3-6 from results JSON only (no raw data needed)."""
import json,numpy as np,matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path
from scipy.stats import beta
R=Path(__file__).resolve().parent/"results"; F=Path(__file__).resolve().parent/"figures"; F.mkdir(exist_ok=True)
J=lambda n:json.load(open(R/n))
BLUE,ORANGE,AQUA,VIOLET,GREY,INK,INK2="#2a78d6","#eb6834","#1baf7a","#6250d6","#9a9893","#0b0b0b","#52514e"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8,"axes.edgecolor":INK2,"axes.labelcolor":INK,"xtick.color":INK2,"ytick.color":INK2,
                     "axes.spines.top":False,"axes.spines.right":False,"axes.linewidth":0.6,"xtick.major.width":0.6,"ytick.major.width":0.6,"pdf.fonttype":42})
def cp(k,n):
    lo=0.0 if k==0 else beta.ppf(0.025,k,n-k+1); hi=1.0 if k==n else beta.ppf(0.975,k+1,n-k); return 100*lo,100*hi
def kn(s): a,b=s.split("/"); return int(a),int(b)
NAMES={"v2_FROZEN":"Proposed (v2)","v1_tieaware":"v1 (tie-aware)","v1.0.1_original":"v1 (original)","global_Mahalanobis":"Global Mahalanobis",
       "PCA_T2":"PCA $T^2$","PCA_SPE":"PCA SPE","IsolationForest":"Isolation forest","physics_CI_conformal":"Physics charge indicator"}
E7=J("e7_e8_paired_operational.json")
# ---------- Figure 3: operating points ----------
fig,axs=plt.subplots(1,2,figsize=(7.2,3.2))
for ax,s,title in zip(axs,("Site2","Site1"),("Site 2: refrigerant undercharge","Site 1: compressor staging")):
    op=E7[s]["operational"]; pts=[]
    for k,v in op.items():
        if k=="v1.0.1_original": continue
        fa,n=kn(v["test_FAR"]); se,m=kn(v["sens"]); x,y=100*fa/n,100*se/m; xl,xh=cp(fa,n); yl,yh=cp(se,m)
        c=BLUE if k=="v2_FROZEN" else (ORANGE if k=="v1_tieaware" else GREY); z=3 if k=="v2_FROZEN" else 2
        ax.errorbar(x,y,xerr=[[x-xl],[xh-x]],yerr=[[y-yl],[yh-y]],fmt="o",ms=6 if c!=GREY else 5,color=c,ecolor=c,elinewidth=0.8,capsize=0,zorder=z,
                    markeredgecolor="white",markeredgewidth=1)
        pts.append((k,x,y))
    # direct labels: detectors at identical operating points share one label
    groups={}
    for k,x,y in pts: groups.setdefault((round(x,2),round(y,2)),[]).append(k)
    OFF={"Site2":{"v1_tieaware":(6,4),"IsolationForest":(6,-9),"PCA_SPE":(6,-3),"global_Mahalanobis":(6,3)},
         "Site1":{"v1_tieaware":(6,6),"PCA_SPE":(6,-10)}}
    for (x,y),ks in groups.items():
        lab=" / ".join(NAMES[k] for k in ks); dx,dy=OFF[s].get(ks[0],(6,-3))
        ax.annotate(lab,(x,y),xytext=(dx,dy),textcoords="offset points",fontsize=6.6,color=INK if ks[0] in("v2_FROZEN","v1_tieaware") else INK2)
    ax.set_title(title,fontsize=8.5,loc="left",color=INK); ax.set_xlabel("Normal test days flagged (%)"); ax.set_ylabel("Fault days detected (%)")
    ax.set_xlim(-2,72 if s=="Site1" else 30); ax.set_ylim(-11 if s=="Site1" else -3,103); ax.grid(axis="y",color="#e6e5e1",lw=0.5); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(F/"Figure_3_operating_points.pdf"); fig.savefig(F/"Figure_3_operating_points.png",dpi=600); plt.close(fig)
# ---------- Figure 4: alarm raster with circuit attribution ----------
E9=J("e9_attribution.json"); order=["v2_FROZEN","v1_tieaware","IsolationForest","global_Mahalanobis","physics_CI_conformal"]
fig,axs=plt.subplots(2,1,figsize=(7.2,3.4),gridspec_kw={"height_ratios":[1,1]})
for ax,s,title in zip(axs,("Site2","Site1"),("Site 2: 27 undercharge fault days (documented: low charge on circuit B)","Site 1: 62 staging fault days (documented: stage 2 will not engage)")):
    op=E7[s]["operational"]; recs=E9[s]["fault_day_records"]; n=len(recs)
    for r,k in enumerate(order):
        seq=op[k]["fault_day_alarm_sequence"]; yy=len(order)-1-r
        for d,ch in enumerate(seq):
            if ch!="1": 
                ax.add_patch(plt.Rectangle((d+0.08,yy+0.12),0.84,0.76,facecolor="none",edgecolor="#d9d8d3",lw=0.4)); continue
            if k=="v2_FROZEN":
                rec=recs[d]; st=rec["stat"][0] if len(rec["stat"])==1 else "max"; c=VIOLET if rec[f"circuit_{st}"]==2 else AQUA
            else: c=GREY
            ax.add_patch(plt.Rectangle((d+0.08,yy+0.12),0.84,0.76,facecolor=c,edgecolor="none"))
    ax.set_xlim(0,n); ax.set_ylim(0,len(order)); ax.set_yticks([len(order)-1-i+0.5 for i in range(len(order))]); ax.set_yticklabels([NAMES[k] for k in order],fontsize=6.8)
    ax.set_xticks(np.arange(0,n,5)+0.5); ax.set_xticklabels(np.arange(1,n+1,5),fontsize=6.5); ax.tick_params(length=0); ax.spines[:].set_visible(False)
    ax.set_title(title,fontsize=8,loc="left",color=INK)
axs[1].set_xlabel("Day of the labelled fault record")
fig.legend(handles=[Patch(facecolor=AQUA,label="Proposed: alarm attributed to circuit 1"),Patch(facecolor=VIOLET,label="Proposed: alarm attributed to circuit 2"),
                    Patch(facecolor=GREY,label="Comparator alarm"),Patch(facecolor="none",edgecolor="#bdbcb6",label="No alarm")],
           loc="lower center",ncol=4,fontsize=6.6,frameon=False,bbox_to_anchor=(0.5,-0.01))
fig.tight_layout(rect=(0,0.06,1,1)); fig.savefig(F/"Figure_4_alarm_raster.pdf"); fig.savefig(F/"Figure_4_alarm_raster.png",dpi=600); plt.close(fig)
# ---------- Figure 5: injection heatmap ----------
E12=J("e12_injection.json"); dets=["v2_FROZEN","v1_tieaware","IsolationForest","global_Mahalanobis","PCA_T2","PCA_SPE"]
fig,axs=plt.subplots(1,2,figsize=(7.2,5.6),sharey=True)
from matplotlib.colors import LinearSegmentedColormap
cmap=LinearSegmentedColormap.from_list("seqblue",["#f4f8fd","#9cc3ef","#2a78d6","#0d3d75"])
for ax,s in zip(axs,("Site2","Site1")):
    sc=E12[s]["scenarios"]; names=list(sc); M=np.array([[kn(sc[n][d]["alarm_days"])[0]/kn(sc[n][d]["alarm_days"])[1] for d in dets] for n in names])*100
    im=ax.imshow(M,aspect="auto",cmap=cmap,vmin=0,vmax=100)
    ax.set_xticks(range(len(dets))); ax.set_xticklabels([NAMES[d].replace(" (","\n(") for d in dets],rotation=90,fontsize=6.5)
    lab=[n.replace("suction_T1","Suction T").replace("discharge_T1","Discharge T").replace("liquid_T1","Liquid-line T").replace("comp_power","Compressor W").replace("|"," ") for n in names]
    ax.set_yticks(range(len(names))); ax.set_yticklabels(lab,fontsize=5.8); ax.tick_params(length=0); ax.spines[:].set_visible(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]): ax.text(j,i,f"{M[i,j]:.0f}",ha="center",va="center",fontsize=4.6,color="white" if M[i,j]>55 else INK)
    ax.set_title(f"{'Site 2' if s=='Site2' else 'Site 1'} ({E12[s]['n_test_days']} normal test days)",fontsize=8,loc="left")
cb=fig.colorbar(im,ax=axs,fraction=0.025,pad=0.02); cb.set_label("Test days alarmed under injection (%)",fontsize=7); cb.ax.tick_params(labelsize=6)
fig.savefig(F/"Figure_6_injection.pdf",bbox_inches="tight"); fig.savefig(F/"Figure_6_injection.png",dpi=600,bbox_inches="tight"); plt.close(fig)
# ---------- Figure 6: ridge sweep ----------
E10b=J("e10b_ridge_sweep.json"); fig,ax=plt.subplots(figsize=(4.2,2.8))
for s,c,lab in (("Site1",BLUE,"Site 1 (of 62 fault days)"),("Site2",ORANGE,"Site 2 (of 27 fault days)")):
    rs=[k for k in E10b[s] if isinstance(E10b[s][k],dict) and "fault_day_sens" in E10b[s][k]]; x=[float(r) for r in rs]; y=[100*kn(E10b[s][r]["fault_day_sens"])[0]/kn(E10b[s][r]["fault_day_sens"])[1] for r in rs]
    ax.plot(x,y,"-o",color=c,lw=2,ms=5,markeredgecolor="white",markeredgewidth=1); ax.annotate(lab,(x[0],y[0]),xytext=(0,7 if s=="Site1" else -12),textcoords="offset points",ha="left",fontsize=7,color=INK)
ax.axvline(1e-3,color=INK2,lw=0.8,ls="--"); ax.text(1.1e-3,30,"frozen ridge",fontsize=6.5,color=INK2)
l3=E10b["Site1"]["joint_cov_eigenvalues_smallest5"][2]; ax.axvline(l3,color=BLUE,lw=0.8,ls=":"); ax.text(l3*0.9,96,"Site 1 $\\lambda_3$",fontsize=6.5,color=INK2,ha="right")
ax.set_xscale("log"); ax.set_xlabel("Covariance ridge"); ax.set_ylabel("Fault days detected (%)"); ax.set_ylim(0,100); ax.grid(axis="y",color="#e6e5e1",lw=0.5)
fig.tight_layout(); fig.savefig(F/"Figure_5_ridge.pdf"); fig.savefig(F/"Figure_5_ridge.png",dpi=600); plt.close(fig)
print("figures written to",F)
