# Tau reconstruction at CMS
The code is a first NN prototype for tau reconstruction at CMS

The code uses tensorflow 2.4.0.

The data used to train comes from a Monte Carlo simulation, where each entry is prepared such to have exactly one tau.

In this code are used the Space Neural Network (SNN) models to reconstruct the decay modes, pt and mass of the tau.

The models and their metrics are implemented in mymodel.py.

The model is trained using NN_training.py, the number of batches and batch size have to be adjusted in mymodel.py. In training.py the training is specified.

To evaluated the model after training was used NN_evaluation.py. In evaluation.py and plotting.py is the effectively done the evaluation.

Input_characteristics.py is used to give the parameters for normalization to mymodel.py.
