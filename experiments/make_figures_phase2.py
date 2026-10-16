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
NAMES={"v2_FROZEN":"Frozen (this paper)","v1_tieaware":"v1 (tie-aware)","v1_tieaware_dual_rule":"v1 (tie-aware)","v1.0.1_original":"v1 (original)","global_Mahalanobis":"Global Mahalanobis",
       "PCA_T2":"PCA $T^2$","PCA_SPE":"PCA SPE","IsolationForest":"Isolation forest","physics_CI_conformal":"Physics charge indicator","physics_cond":"Physics (cond.-dependent)"}
E7=J("e7_e8_paired_operational.json")
# ---------- Figure 3: operating points, single-maximum rule vs two-statistic rule ----------
E14=J("e14_equal_budget.json")
MAP14={"v1_tieaware":"v1_tieaware_dual_rule","global_Mahalanobis":"global_Mahalanobis","PCA_T2":"PCA_T2","PCA_SPE":"PCA_SPE","IsolationForest":"IsolationForest"}
fig,axs=plt.subplots(1,2,figsize=(7.2,3.4))
for ax,s,title in zip(axs,("Site2","Site1"),("Site 2: refrigerant undercharge","Site 1: compressor staging")):
    op=E7[s]["operational"]; d14=E14[s]["comparators_dual_rule"]
    for k,k14 in MAP14.items():
        fa,n=kn(op[k]["test_FAR"]); se,m=kn(op[k]["sens"]); x0,y0=100*fa/n,100*se/m
        fa,n=kn(d14[k14]["test_dayFAR"]); se,m=kn(d14[k14]["fault_day_sens"]); x1,y1=100*fa/n,100*se/m
        c=ORANGE if k=="v1_tieaware" else GREY
        ax.annotate("",xy=(x1,y1),xytext=(x0,y0),arrowprops=dict(arrowstyle="-|>",color=c,lw=0.9,shrinkA=3,shrinkB=3))
        ax.plot(x0,y0,"o",ms=5,mfc="white",mec=c,mew=1.2,zorder=3); ax.plot(x1,y1,"o",ms=5,color=c,mec="white",mew=0.8,zorder=3)
        off={("Site2","global_Mahalanobis"):(4,-11),("Site2","IsolationForest"):(5,2),("Site1","PCA_SPE"):(5,-9)}.get((s,k),(5,-3))
        ax.annotate(NAMES[k],(x1,y1),xytext=off,textcoords="offset points",fontsize=6.4,color=INK2)
    fa,n=kn(op["v2_FROZEN"]["test_FAR"]); se,m=kn(op["v2_FROZEN"]["sens"]); x,y=100*fa/n,100*se/m; xl,xh=cp(fa,n); yl,yh=cp(se,m)
    ax.errorbar(x,y,xerr=[[x-xl],[xh-x]],yerr=[[y-yl],[yh-y]],fmt="o",ms=6.5,color=BLUE,ecolor=BLUE,elinewidth=0.8,mec="white",mew=1,zorder=4)
    ax.annotate("Frozen (this paper)",(x,y),xytext=(6,4),textcoords="offset points",fontsize=6.8,color=INK)
    ax.set_title(title,fontsize=8.5,loc="left",color=INK); ax.set_xlabel("Normal test days flagged (%)"); ax.set_ylabel("Fault days detected (%)")
    ax.set_xlim(-2,50 if s=="Site1" else 26); ax.set_ylim(-4,103); ax.grid(axis="y",color="#e6e5e1",lw=0.5); ax.set_axisbelow(True)
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([],[],marker="o",ls="",mfc="white",mec=GREY,label="Comparator, daily-maximum rule at $\\alpha$"),
                    Line2D([],[],marker="o",ls="",color=GREY,label="Same comparator, daily maximum and mean at $\\alpha/2$ (frozen detector's rule)")],
           loc="lower center",ncol=2,fontsize=6.6,frameon=False)
fig.tight_layout(rect=(0,0.07,1,1)); fig.savefig(F/"Figure_3_operating_points.pdf"); fig.savefig(F/"Figure_3_operating_points.png",dpi=600); plt.close(fig)
# ---------- Figure 4: alarm raster with circuit attribution ----------
E9=J("e9_attribution.json"); order=["v2_FROZEN","v1_tieaware","IsolationForest","global_Mahalanobis","physics_CI_conformal"]
fig,axs=plt.subplots(2,1,figsize=(7.2,3.4),gridspec_kw={"height_ratios":[1,1]})
for ax,s,title in zip(axs,("Site2","Site1"),("Site 2: 27 undercharge fault days (documented: low charge on circuit B)","Site 1: 62 staging fault days (documented: stage 2 will not engage)")):
    op=E7[s]["operational"]; recs=E9[s]["fault_day_records"]; n=len(recs)
    E14s=E14[s]["comparators_dual_rule"]; MAPR={"v1_tieaware":"v1_tieaware_dual_rule","IsolationForest":"IsolationForest","global_Mahalanobis":"global_Mahalanobis","physics_CI_conformal":"physics_condition_dependent_dual_rule"}
    for r,k in enumerate(order):
        seq=op[k]["fault_day_alarm_sequence"] if k=="v2_FROZEN" else E14s[MAPR[k]]["fault_day_alarm_sequence"]; yy=len(order)-1-r
        for d,ch in enumerate(seq):
            if ch!="1": 
                ax.add_patch(plt.Rectangle((d+0.08,yy+0.12),0.84,0.76,facecolor="none",edgecolor="#d9d8d3",lw=0.4)); continue
            if k=="v2_FROZEN":
                rec=recs[d]; st=rec["stat"][0] if len(rec["stat"])==1 else "max"; c=VIOLET if rec[f"circuit_{st}"]==2 else AQUA
            else: c=GREY
            ax.add_patch(plt.Rectangle((d+0.08,yy+0.12),0.84,0.76,facecolor=c,edgecolor="none"))
    ax.set_xlim(0,n); ax.set_ylim(0,len(order)); ax.set_yticks([len(order)-1-i+0.5 for i in range(len(order))]); ax.set_yticklabels([("Physics (condition-dep.)" if k=="physics_CI_conformal" else NAMES[k]) for k in order],fontsize=6.8)
    ax.set_xticks(np.arange(0,n,5)+0.5); ax.set_xticklabels(np.arange(1,n+1,5),fontsize=6.5); ax.tick_params(length=0); ax.spines[:].set_visible(False)
    ax.set_title(title,fontsize=8,loc="left",color=INK)
axs[1].set_xlabel("Day of the labelled fault record")
fig.legend(handles=[Patch(facecolor=AQUA,label="Frozen: alarm attributed to circuit 1"),Patch(facecolor=VIOLET,label="Frozen: alarm attributed to circuit 2"),
                    Patch(facecolor=GREY,label="Comparator alarm"),Patch(facecolor="none",edgecolor="#bdbcb6",label="No alarm")],
           loc="lower center",ncol=4,fontsize=6.6,frameon=False,bbox_to_anchor=(0.5,-0.01))
fig.tight_layout(rect=(0,0.06,1,1)); fig.savefig(F/"Figure_4_alarm_raster.pdf"); fig.savefig(F/"Figure_4_alarm_raster.png",dpi=600); plt.close(fig)
# ---------- Figure 5: injection heatmap ----------
E12=J("e12b_injection_equal_budget.json"); dets=["v2_FROZEN","v1_tieaware_dual_rule","IsolationForest","global_Mahalanobis","PCA_T2","PCA_SPE"]
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
    ax.set_title(f"{'Site 2' if s=='Site2' else 'Site 1'} ({44 if s=='Site2' else 13} normal test days)",fontsize=8,loc="left")
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
