import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pp
import seaborn as sns
import numpy as np

def plot_metrics(history, n_epoch):
    epochs = history.epoch
    hist = pd.DataFrame(history.history)
    loss = hist["loss"]
    acc = hist["accuracy"]
    loss_val = hist["val_loss"]
    acc_val = hist["val_accuracy"]

    fig0, axes = plt.subplots(2, sharex=False, figsize=(12, 8))
    fig0.suptitle('Metrics')
    axes[0].set_ylabel("Loss", fontsize=14)
    axes[0].set_xlabel("Epoch", fontsize=14)
    axes[0].set_xticks(np.arange(0, n_epoch, 1.0))
    axes[0].plot(epochs, loss, 'bo--', label="loss")
    axes[0].plot(epochs, loss_val, 'ro--', label="val loss")
    axes[0].legend()
    axes[1].set_ylabel("Accuracy", fontsize=14)
    axes[1].set_xlabel("Epoch", fontsize=14)
    axes[1].set_xticks(np.arange(0, n_epoch, 1.0))
    axes[1].plot(epochs, acc, 'bo--', label="accuracy")
    axes[1].plot(epochs, acc_val, 'ro--', label=" val accuracy")
    axes[1].legend()
    plt.show()
    pdf0 = pp.PdfPages("./Plots/Metrics.pdf")
    pdf0.savefig(fig0)
    pdf0.close()
    plt.close()

### Confusion matrix of decay modes:
def plt_conf_dm(conf_dm_mat, old = False):
    x_axis_labels = ['$\pi^{\pm}$','$\pi^{\pm} + \pi^0$', '$\pi^{\pm} + 2\pi^0$', \
                 '$\pi^{\pm} + 3\pi^0$','$3\pi^{\pm}$', '$3\pi^{\pm} + 1\pi^0$',\
                 '$3\pi^{\pm} + 2\pi^0$', 'others'] # labels for x-axis
    y_axis_labels = x_axis_labels # labels for y-axis

    fig = plt.figure(figsize=(8,5),dpi=100)
    sns.heatmap(conf_dm_mat,xticklabels=x_axis_labels, yticklabels=y_axis_labels, cmap='YlGnBu', annot=True, fmt="3.0f")
    plt.ylim(-0.5,9.5)
    plt.xlim(-0.5,9.5)
    if old == False:
        plt.ylabel('True decay mode',fontsize = 16)
    else:
        plt.ylabel('Old reconstruction decay mode',fontsize = 16)
    plt.xlabel('Predicted decay mode',fontsize = 16)
    plt.tight_layout()
    plt.show()
    plt.close()
    if old == False:
        pdf = pp.PdfPages("./Plots/conf_dm_mat.pdf")
    else: 
        pdf = pp.PdfPages("./Plots/conf_dm_mat_old.pdf")
    pdf.savefig(fig)
    pdf.close()

    # ### check the true distribution of the decay modes:
    # tot_dm = conf_dm_mat.sum(axis=1)
    # print('\n Total number of events with a decay mode for true, corresponds to [0,1,2,3,...] decay mode: \n',tot_dm,'\n') 
    # tot_dm_norm = tot_dm/tot_dm.sum()
    # print('Probabilities of decay mode for true: \n',tot_dm_norm,'\n')


### Accuracy calculation:
def accuracy_calc(conf_dm_mat):
    ## Normalization of cond_dm_mat:
    conf_dm_mat_norm = conf_dm_mat
    for i in range(0,len(conf_dm_mat[0,:])):
        summy = 0
        summy = conf_dm_mat[i,:].sum() # sum of line => normalize lines
        if (summy != 0):
            conf_dm_mat_norm[i,:] = conf_dm_mat[i,:]/summy

    # fig = plt.figure(figsize=(5,5))
    # sns.heatmap(conf_dm_mat_norm, cmap='YlGnBu', annot=True, fmt="3.0f")
    # plt.ylim(-0.5,23.5)
    # plt.xlim(-0.5,23.5)
    # plt.ylabel('True decay mode',fontsize = 16)
    # plt.xlabel('Predicted decay mode',fontsize = 16)
    # plt.show()
    # plt.close()
    # pdf = pp.PdfPages("./Plots/conf_dm_mat_norm.pdf")
    # pdf.savefig(fig)
    # pdf.close()

    ## Accuracy extraction for important decay modes:
    accuracy = np.zeros(7)
    for i in range(0,7):
        accuracy[i] = conf_dm_mat_norm[i,i]

    return accuracy


#################################################################################

# ### Confusion matrix of charged count:
# def plt_conf_charge(conf_matrix):
#     conf_mat_1 = np.zeros((6,6))

#     for i in range(0,6):
#         for j in range(0,6):
#             conf_mat_1 += conf_matrix[:,i,:,j]

#     fig = plt.figure(figsize=(5,5))
#     sns.heatmap(conf_mat_1, cmap='YlGnBu', annot=True, fmt="3.0f")
#     plt.ylim(-0.5,6.5)
#     plt.xlim(-0.5,6.5)
#     plt.ylabel('True charge counts',fontsize = 16)
#     plt.xlabel('Predicted charge counts',fontsize = 16)
#     # plt.show()
#     plt.close()
#     pdf = pp.PdfPages("./Plots/conf_mat_charged.pdf")
#     pdf.savefig(fig)
#     pdf.close()

# ### Confusion matrix of neutral count:
# def plt_conf_neutral(conf_matrix):
#     conf_mat_1 = np.zeros((6,6))

#     for i in range(0,6):
#         for j in range(0,6):
#             conf_mat_1 += conf_matrix[i,:,j,:]

#     fig = plt.figure(figsize=(5,5))
#     sns.heatmap(conf_mat_1, cmap='YlGnBu', annot=True, fmt="3.0f")
#     plt.ylim(-0.5,6.5)
#     plt.xlim(-0.5,6.5)
#     plt.ylabel('True neutral counts',fontsize = 16)
#     plt.xlabel('Predicted neutral counts',fontsize = 16)
#     # plt.show()
#     plt.close()
#     pdf = pp.PdfPages("./Plots/conf_mat_neutral.pdf")
#     pdf.savefig(fig)
#     pdf.close()