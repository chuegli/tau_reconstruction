import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pp
import seaborn as sns
import numpy as np
import ROOT as R

from mymodel_copy import *

### Plots the loss and accuracy for the trainset and the validationset:
def plot_metrics(history):
    epochs = history.epoch
    hist   = pd.DataFrame(history.history)
    # print('\nPrint history: ',history.history)
    # for i in history.history:
    #     print(i)

    fig0, axes = plt.subplots(2, sharex=False, figsize=(12, 8))
    fig0.suptitle('Metrics')
    axes[0].set_ylabel("Loss", fontsize=14)
    axes[0].set_xlabel("Epoch", fontsize=14)
    axes[0].set_xticks(np.arange(0, n_epoch, 1.0))
    axes[0].plot(epochs, hist["loss"], 'bo--', label="loss")
    axes[0].plot(epochs, hist["val_loss"] , 'ro--', label="val loss")
    axes[0].legend()
    axes[1].set_ylabel("Accuracy", fontsize=14)
    axes[1].set_xlabel("Epoch", fontsize=14)
    axes[1].set_xticks(np.arange(0, n_epoch, 1.0))
    axes[1].plot(epochs, hist["my_acc"], 'bo--', label="accuracy")
    axes[1].plot(epochs, hist["val_my_acc"], 'ro--', label=" val accuracy")
    axes[1].legend()
    # plt.show()

    # fig1, axes = plt.subplots(2, sharex=False, figsize=(12, 8))
    # fig1.suptitle('Resolutions') 
    # axes[0].set_xticks(np.arange(0, n_epoch, 1.0)) 
    # axes[0].plot(epochs, hist["pt_res"]    , 'bo--', label="pt_res") 
    # axes[0].plot(epochs, hist["m2_res"]    , 'ro--', label="m2_res")
    # axes[0].plot(epochs, hist["val_pt_res"], 'b*:', label="val_pt_res") 
    # axes[0].plot(epochs, hist["val_m2_res"], 'r*:', label="val_m2_res") 
    # axes[0].legend()
    # axes[1].set_xticks(np.arange(0, n_epoch, 1.0)) 
    # axes[1].plot(epochs, hist["phi_res"]    , 'go--', label="phi_res") 
    # axes[1].plot(epochs, hist["eta_res"]    , 'mo--', label="eta_res") 
    # axes[1].plot(epochs, hist["val_phi_res"], 'g*:', label="val_phi_res") 
    # axes[1].plot(epochs, hist["val_eta_res"], 'm*:', label="val_eta_res") 
    # axes[1].legend()
    

    pdf0 = pp.PdfPages("../Plots/Metrics.pdf")
    pdf0.savefig(fig0)
    # pdf0.savefig(fig1)
    pdf0.close()
    plt.close()


### Plots the confusion matrix of decay modes:
def plt_conf_dm(conf_dm_mat, old = False):
    print('ciao 0')
    x_axis_labels = ['$\pi^{\pm}$','$\pi^{\pm} + \pi^0$', '$\pi^{\pm} + 2\pi^0$', \
                 '$\pi^{\pm} + 3\pi^0$','$3\pi^{\pm}$', '$3\pi^{\pm} + 1\pi^0$',\
                 '$3\pi^{\pm} + 2\pi^0$', 'others'] # labels for x-axis
    y_axis_labels = x_axis_labels # labels for y-axis

    # fig = plt.figure(figsize=(8,5),dpi=100)
    print('ciao 1')
    plt.title("Decay modes")
    sns.heatmap(conf_dm_mat,xticklabels=x_axis_labels, yticklabels=y_axis_labels, cmap='YlGnBu', annot=True, fmt="3.0f")
    print('ciao 1.1')
    plt.ylim(-0.5,9.5)
    plt.xlim(-0.5,9.5)
    plt.ylabel('True',fontsize = 16)
    if old == False:
        plt.xlabel('Predicted',fontsize = 16)
    else:
        plt.xlabel('Default tau reconstruction',fontsize = 16)
    plt.tight_layout()
    # plt.show()
    print('ciao 2')
    if old == False:
        plt.savefig("../Plots/conf_dm_mat.pdf")
        # pdf = pp.PdfPages("../Plots/conf_dm_mat.pdf")
    else: 
        plt.savefig("../Plots/conf_dm_mat_old.pdf")
        # pdf = pp.PdfPages("../Plots/conf_dm_mat_old.pdf")
    # pdf.savefig(fig)
    # pdf.close()
    # plt.close()

    # ### check the true distribution of the decay modes:
    # tot_dm = conf_dm_mat.sum(axis=1)
    # print('\n Total number of events with a decay mode for true, corresponds to [0,1,2,3,...] decay mode: \n',tot_dm,'\n') 
    # tot_dm_norm = tot_dm/tot_dm.sum()
    # print('Probabilities of decay mode for true: \n',tot_dm_norm,'\n')

def accuracy_calc(conf_dm_mat, old = False):
    ## Normalization of cond_dm_mat:
    conf_dm_mat_norm = conf_dm_mat
    for i in range(0,len(conf_dm_mat[0,:])):
        summy = 0
        summy = conf_dm_mat[i,:].sum() # sum of line => normalize lines
        if (summy != 0):
            conf_dm_mat_norm[i,:] = conf_dm_mat[i,:]/summy

    x_axis_labels = ['$\pi^{\pm}$','$\pi^{\pm} + \pi^0$', '$\pi^{\pm} + 2\pi^0$', \
                 '$\pi^{\pm} + 3\pi^0$','$3\pi^{\pm}$', '$3\pi^{\pm} + 1\pi^0$',\
                 '$3\pi^{\pm} + 2\pi^0$', 'others'] # labels for x-axis
    y_axis_labels = x_axis_labels # labels for y-axis

    fig = plt.figure(figsize=(8,5))
    plt.title("Decay modes")
    sns.heatmap(conf_dm_mat_norm, xticklabels=x_axis_labels, yticklabels=y_axis_labels, cmap='YlGnBu', annot=True, fmt="3.2f")
    plt.ylim(-0.5,9.5)
    plt.xlim(-0.5,9.5)
    plt.ylabel('True',fontsize = 16)
    if (old == False):
        plt.xlabel('Predicted',fontsize = 16)
    else:
        plt.xlabel('Default tau reconstruction',fontsize = 16)
    plt.tight_layout()
    # plt.show()
    if(old==False):
        pdf = pp.PdfPages("../Plots/conf_dm_mat_norm.pdf")
    else:
        pdf = pp.PdfPages("../Plots/conf_dm_mat_norm_old.pdf")
    pdf.savefig(fig)
    pdf.close()
    plt.close()

    ## Accuracy extraction for important decay modes:
    accuracy = np.zeros(8)
    # weights = np.array([0.1151, 0.2593, 0.1081, 0.0118, 0.0980, 0.0476, 0.0051, 0.0029])
    # weights = weights/weights.sum()
    accuracy_value = 0
    for i in range(0,8):
        accuracy[i] = conf_dm_mat_norm[i,i]
        # accuracy_value += weights[i]*accuracy[i]
        accuracy_value += accuracy[i]

    return accuracy_value


def plot_res(h, def_h, xlabelname, c_dm = False):
    def_h.SetXTitle(xlabelname)
    R.gStyle.SetOptStat('rme')
    if(c_dm == True):
        def_h.SetTitle("Decay mode: true = predicted")
    else:
        def_h.SetTitle(" ")
    def_h.SetLineColor(R.kRed)
    h.SetLineColor(R.kBlue)

    def_h.Draw("h")
    h.Draw("h sames")
    R.gPad.Update()

    st = h.FindObject("stats")
    st.SetLineColor(R.kBlue)
    st.SetX1NDC(0.69)
    st.SetY1NDC(0.74)
    st.SetX2NDC(0.89)
    st.SetY2NDC(0.89)
    st1 = def_h.FindObject("stats")
    st1.SetLineColor(R.kRed)
    st1.SetX1NDC(0.69)
    st1.SetY1NDC(0.58)
    st1.SetX2NDC(0.89)
    st1.SetY2NDC(0.73)

    legend = R.TLegend(0.15,0.75,0.25,0.85) 
    legend.AddEntry(h    ," ML reco","f") 
    legend.AddEntry(def_h," Default reco","f") 
    legend.SetBorderSize(0)
    legend.SetFillColor(0)
    legend.SetFillStyle(0)
    legend.SetTextFont(42)
    legend.SetTextSize(0.035)
    return legend