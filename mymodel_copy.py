import ROOT as R
import tensorflow as tf
import numpy as np
from tensorflow import keras
import json
from ROOT import TLorentzVector
import math
# import spektral
# import matplotlib.pyplot as plt

### All the parameters:
n_tau    = 100 # number of taus (or events) per batch
n_pf     = 100 #100 # number of pf candidates per event
n_fe     = 29#31   # total muber of features: 24
n_labels = 6    # number of labels per event
n_epoch  = 5 #100  # number of epochs on which to train
n_steps_val   = 14213
n_steps_test  = 63970  # number of steps in the evaluation: (events in conf_dm_mat) = n_steps * n_tau
entry_start   = 0
entry_stop    = 6396973 # total number of events in the dataset = 14'215'297
# 45% = 6'396'973
# 10% = 1'421'351 (approximative calculations have been rounded)
entry_start_val  = entry_stop +1
print('Entry_start_val:', entry_start_val)
entry_stop_val   = entry_stop + n_tau*n_steps_val + 1
print('Entry_stop_val: ',entry_stop_val)
# entry_start_test = entry_stop_val+1
entry_start_test  = entry_stop_val  + 1
entry_stop_test  = entry_start_test + n_tau*n_steps_test
print('Entry_stop_test (<= 14215297): ',entry_stop_test)



class StdLayer(tf.keras.layers.Layer):
    def __init__(self, file_name, var_pos, n_sigmas, **kwargs):
        with open(file_name) as json_file:
            data_json = json.load(json_file)
        n_vars = len(var_pos)
        self.vars_std = [1] * n_vars
        self.vars_mean = [1] * n_vars
        self.vars_apply = [False] * n_vars
        for var, ms in data_json.items(): 
            pos = var_pos[var]
            self.vars_mean[pos]  = ms[0]['mean']
            self.vars_std[pos]   = ms[0]['std']
            self.vars_apply[pos] = True
        self.vars_mean  = tf.constant(self.vars_mean,  dtype=tf.float32)
        self.vars_std   = tf.constant(self.vars_std,   dtype=tf.float32)
        self.vars_apply = tf.constant(self.vars_apply, dtype=tf.bool)
        self.n_sigmas   = n_sigmas

        super(StdLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        super(StdLayer, self).build(input_shape)

    def call(self, X):
        Y = tf.clip_by_value(( X - self.vars_mean ) / self.vars_std, -self.n_sigmas, self.n_sigmas)
        return tf.where(self.vars_apply, Y, X)

class ScaleLayer(tf.keras.layers.Layer):
    def __init__(self, file_name, var_pos, interval_to_scale, **kwargs):
        with open(file_name) as json_file:
            data_json = json.load(json_file)
        self.a = interval_to_scale[0]
        self.b = interval_to_scale[1]
        n_vars = len(var_pos)
        self.vars_max   = [1] * n_vars
        self.vars_min   = [1] * n_vars
        self.vars_apply = [False] * n_vars
        for var, mm in data_json.items():
            pos = var_pos[var]
            self.vars_min[pos]   = mm[0]['min']
            self.vars_max[pos]   = mm[0]['max']
            self.vars_apply[pos] = True
        self.vars_min   = tf.constant(self.vars_min,   dtype=tf.float32)
        self.vars_max   = tf.constant(self.vars_max,   dtype=tf.float32)
        self.vars_apply = tf.constant(self.vars_apply, dtype=tf.bool)
        self.y = (self.b - self.a) / (self.vars_max - self.vars_min)

        super(ScaleLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        super(ScaleLayer, self).build(input_shape)

    def call(self, X):
        Y = tf.clip_by_value( (self.y * ( X - self.vars_min))  + self.a , self.a, self.b)
        return tf.where(self.vars_apply, Y, X)

class MyModel(tf.keras.Model):
    def __init__(self, map_features, **kwargs):
        super(MyModel, self).__init__(**kwargs)
        self.px_index    = map_features["pfCand_px"] 
        self.py_index    = map_features["pfCand_py"] 
        self.pz_index    = map_features["pfCand_pz"]
        self.E_index     = map_features["pfCand_E"] 
        self.valid_index = map_features["pfCand_valid"]
        self.map_features = map_features

        self.embedding1   = tf.keras.layers.Embedding(350,2)
        self.embedding2   = tf.keras.layers.Embedding(4  ,2)
        self.embedding3   = tf.keras.layers.Embedding(8  ,2)
        self.normalize    = StdLayer('mean_std.txt', map_features, 5, name='std_layer')
        self.scale        = ScaleLayer('min_max.txt', map_features, [-1,1], name='scale_layer')
        self.flatten      = tf.keras.layers.Flatten() # flattens a ND array to a 2D array

        self.n_layers = 5 #10
        self.dense = []
        self.dropout_dense = []
        self.batch_norm_dense = []
        self.acti_dense = []
        
        for i in range(0,self.n_layers):
            self.dense.append(tf.keras.layers.Dense(3600, name='dense_{}'.format(i)))
            self.batch_norm_dense.append(tf.keras.layers.BatchNormalization(name='batch_normalization_{}'.format(i)))
            self.acti_dense.append(tf.keras.layers.Activation('relu', name='acti_dense_{}'.format(i)))
            self.dropout_dense.append(tf.keras.layers.Dropout(0.25,name='dropout_dense_{}'.format(i)))
        
        self.output_layer_2   = tf.keras.layers.Dense(2  , name='output_layer_2') 
        self.output_layer_100 = tf.keras.layers.Dense(100, name='output_layer_100', activation='softmax') 

    @tf.function
    def call(self, xx):
        x_em1 = self.embedding1(tf.abs(xx[:,:,self.map_features['pfCand_pdgId']]))
        x_em2 = self.embedding2(tf.abs(xx[:,:,self.map_features['pfCand_fromPV']]))
        x_em3 = self.embedding3(tf.abs(xx[:,:,self.map_features['pfCand_pvAssociationQuality']]))
        x = self.normalize(xx)
        x = self.scale(x)

        x_part1 = x[:,:,:self.map_features['pfCand_pdgId']]
        x_part2 = x[:,:,(self.map_features["pfCand_fromPV"]+1):]
        x = tf.concat((x_part1,x_part2,x_em1,x_em2,x_em3),axis = 2)

        x = self.flatten(x)
        for i in range(0,self.n_layers):
            x = self.dense[i](x)
            x = self.batch_norm_dense[i](x)
            x = self.acti_dense[i](x)
            x = self.dropout_dense[i](x)
        x2   = self.output_layer_2(x)
        x100 = self.output_layer_100(x)
        # print('x100.shape: ', x100.shape)
        # print('x2.shape: ', x2.shape)

        ### 4-momentum:
        mypxs  = xx[:,:,self.px_index] * x100 * xx[:,:,self.valid_index]
        mypys  = xx[:,:,self.py_index] * x100 * xx[:,:,self.valid_index]
        mypzs  = xx[:,:,self.pz_index] * x100 * xx[:,:,self.valid_index]
        myEs   = xx[:,:,self.E_index]  * x100 * xx[:,:,self.valid_index]

        mypx   = tf.reduce_sum(mypxs, axis = 1)
        mypy   = tf.reduce_sum(mypys, axis = 1)
        mypz   = tf.reduce_sum(mypzs, axis = 1)
        myE    = tf.reduce_sum(myEs , axis = 1)

        mypx2  = tf.square(mypx)
        mypy2  = tf.square(mypy)
        mypz2  = tf.square(mypz)

        mypt   = tf.sqrt(mypx2 + mypy2)
        mymass = tf.square(myE) - mypx2 - mypy2 - mypz2
        absp   = tf.sqrt(mypx2 + mypy2 + mypz2)

        ### for myeta and myphi:
        myphi = mypt*0.0
        myeta = mypt*0.0

        cosTheta = tf.where(absp==0, 1.0, mypz/absp)
        myeta = tf.where(cosTheta*cosTheta < 1, -0.5*tf.math.log((1.0-cosTheta)/(1.0+cosTheta)), 0.0)
        myphi = tf.where(tf.math.logical_and(mypx == 0, mypy == 0), 0.0, tf.math.atan2(mypy, mypx))

        xx20 = x2[:,0] # is needed doesn't like direct input
        xx21 = x2[:,1]

        xout = tf.stack([xx20,xx21,mypt,myeta,myphi,mymass], axis=1)

        return xout


class MyGNN(tf.keras.Model):

    def __init__(self, map_features, **kwargs):
        super(MyGNN, self).__init__(**kwargs)
        self.px_index     = map_features["pfCand_px"] 
        self.py_index     = map_features["pfCand_py"] 
        self.pz_index     = map_features["pfCand_pz"]
        self.E_index      = map_features["pfCand_E"] 
        self.valid_index  = map_features["pfCand_valid"]
        self.map_features = map_features

        self.embedding1   = tf.keras.layers.Embedding(350,2)
        self.embedding2   = tf.keras.layers.Embedding(4  ,2)
        self.embedding3   = tf.keras.layers.Embedding(8  ,2)
        self.normalize    = StdLayer('mean_std.txt', map_features, 5, name='std_layer')
        self.scale        = ScaleLayer('min_max.txt', map_features, [-1,1], name='scale_layer')
        self.flatten      = tf.keras.layers.Flatten() # flattens a ND array to a 2D array

        self.n_layers = 5 #10
        self.dense = []
        self.dropout_dense = []
        self.batch_norm_dense = []
        self.acti_dense = []
        
        for i in range(0,self.n_layers):
            self.dense.append(tf.keras.layers.Dense(3600, name='dense_{}'.format(i)))
            self.batch_norm_dense.append(tf.keras.layers.BatchNormalization(name='batch_normalization_{}'.format(i)))
            self.acti_dense.append(tf.keras.layers.Activation('relu', name='acti_dense_{}'.format(i)))
            self.dropout_dense.append(tf.keras.layers.Dropout(0.25,name='dropout_dense_{}'.format(i)))
        
        self.output_layer_2   = tf.keras.layers.Dense(2  , name='output_layer_2') 
        self.output_layer_100 = tf.keras.layers.Dense(100, name='output_layer_100', activation='softmax') 

        self.coord_2D = tf.keras.layers.Dense(2  , name='coord_2D') 

    # @tf.function
    def call(self, xx):
        x_em1 = self.embedding1(tf.abs(xx[:,:,self.map_features['pfCand_pdgId']]))
        x_em2 = self.embedding2(tf.abs(xx[:,:,self.map_features['pfCand_fromPV']]))
        x_em3 = self.embedding3(tf.abs(xx[:,:,self.map_features['pfCand_pvAssociationQuality']]))
        x = self.normalize(xx)
        x = self.scale(x)

        x_part1 = x[:,:,:self.map_features['pfCand_pdgId']]
        x_part2 = x[:,:,(self.map_features["pfCand_fromPV"]+1):]
        x = tf.concat((x_em1,x_em2,x_em3,x_part1,x_part2),axis = 2)
        # print('x.shape 1: ', x.shape)

        
        for pf_ind in range(0,n_pf):
            if(pf_ind == 0):
                x_shape = tf.shape(x[:,:,self.map_features['pfCand_rel_eta']])
                diff_eta_1 = tf.reshape(x[:,pf_ind,self.map_features['pfCand_rel_eta']],(x_shape[0],1))
                diff_eta = x[:,:,self.map_features['pfCand_rel_eta']]-diff_eta_1
                diff_phi_1 = tf.reshape(x[:,pf_ind,self.map_features['pfCand_rel_phi']],(x_shape[0],1))
                diff_phi = x[:,:,self.map_features['pfCand_rel_phi']]-diff_phi_1
            else:
                diff_eta_1 = tf.reshape(c2[:,pf_ind,0],(x_shape[0],1))
                diff_eta = c2[:,:,0]-diff_eta_1
                diff_phi_1 = tf.reshape(c2[:,pf_ind,1],(x_shape[0],1))
                diff_phi = c2[:,:,0]-diff_phi_1
            diff_eta = tf.math.square(diff_eta)
            diff_phi = tf.math.square(diff_phi)
            dist = tf.math.sqrt( diff_eta + diff_phi )
            # print('dist.shape: ', dist.shape)
            top_probs, res = tf.math.top_k(-dist, k = 11) # finds the neighbours of the pfcand
            # print('res.shape: ',res.shape) # (n_tau, 11)
            # print(res)
            s = select_cand(x, res) # creates s with pfcand and its 10 neighbours
            # print('s.shape beginning 1: ',s.shape) # s.shape should be (11,31-3+3*2=34)
            s = self.flatten(s)
            # print('s.shape beginning 2: ',s.shape)
            for i in range(0,self.n_layers):
                s = self.dense[i](s)
                s = self.batch_norm_dense[i](s)
                s = self.acti_dense[i](s)
                s = self.dropout_dense[i](s)
            c2 = self.coord_2D(s) # not good has shape (6,2) not (6,100,2)
            print('c2.shape ending: ',c2.shape) # s.shape should be (1,35)


        ## Extract the closest particles in a distance 0.5?
        r = 1.5
        distance = tf.math.sqrt(  tf.math.square(x[:,:,self.map_features['pfCand_rel_eta']]) \
                                + tf.math.square(x[:,:,self.map_features['pfCand_rel_phi']]) )
        good_bool_1 = tf.math.greater(-distance, -r) 
        good_bool = tf.math.logical_and(good_bool_1,distance != 0)
        good_ones = tf.where(good_bool, 1, 0)
        print('good_ones.shape: ',good_ones.shape)
        print('good_ones: ',good_ones)

        ### End GNN part

        x2   = self.output_layer_2(x)
        x100 = self.output_layer_100(x)

        ### 4-momentum:
        mypxs  = xx[:,:,self.px_index] * x100 * xx[:,:,self.valid_index]
        mypys  = xx[:,:,self.py_index] * x100 * xx[:,:,self.valid_index]
        mypzs  = xx[:,:,self.pz_index] * x100 * xx[:,:,self.valid_index]
        myEs   = xx[:,:,self.E_index]  * x100 * xx[:,:,self.valid_index]

        mypx   = tf.reduce_sum(mypxs, axis = 1)
        mypy   = tf.reduce_sum(mypys, axis = 1)
        mypz   = tf.reduce_sum(mypzs, axis = 1)
        myE    = tf.reduce_sum(myEs , axis = 1)

        mypx2  = tf.square(mypx)
        mypy2  = tf.square(mypy)
        mypz2  = tf.square(mypz)

        mypt   = tf.sqrt(mypx2 + mypy2)
        mymass = tf.square(myE) - mypx2 - mypy2 - mypz2
        absp   = tf.sqrt(mypx2 + mypy2 + mypz2)

        ### for myeta and myphi:
        myphi = mypt*0.0
        myeta = mypt*0.0

        cosTheta = tf.where(absp==0, 1.0, mypz/absp)
        myeta = tf.where(cosTheta*cosTheta < 1, -0.5*tf.math.log((1.0-cosTheta)/(1.0+cosTheta)), 0.0)
        myphi = tf.where(tf.math.logical_and(mypx == 0, mypy == 0), 0.0, tf.math.atan2(mypy, mypx))

        xx20 = x2[:,0] # is needed doesn't like direct input
        xx21 = x2[:,1]

        xout = tf.stack([xx20,xx21,mypt,myeta,myphi,mymass], axis=1)

        return xout 


### Function that creates generators:
def make_generator(file_name, entry_begin, entry_end, z = False):
    _data_loader = R.DataLoader(file_name, n_tau, entry_begin, entry_end)
    _n_batches   = _data_loader.NumberOfBatches()

    def _generator():
        cnt = 0
        while True:
            _data_loader.Reset()
            while _data_loader.HasNext(): 
                # print('hello 1')
                data = _data_loader.LoadNext()
                # print('hello 2')
                x_np = np.asarray(data.x)
                x_3d = x_np.reshape((n_tau, n_pf, n_fe))
                y_np = np.asarray(data.y)
                y_2d = y_np.reshape((n_tau, n_labels))
                if z == True:
                    z_np = np.asarray(data.z)
                    z_2d = z_np.reshape((n_tau, n_labels-1))
                    yield x_3d, y_2d, z_2d
                else:
                    yield x_3d, y_2d
            ++cnt
            if cnt == 100: 
                gc.collect() # garbage collection to improve preformance
                cnt = 0
    
    return _generator, _n_batches

#############################################################################################
##### Custom metrics:
### Accuracy calculation for number of charged/neutral hadrons:
@tf.function
def my_acc(y_true, y_pred):
    # print('\naccuracy calcualtion:')
    y_true = tf.math.round(y_true)
    y_true_int = tf.cast(y_true, tf.int32)
    y_pred = tf.math.round(y_pred)
    y_pred_int = tf.cast(y_pred, tf.int32)
    result = tf.math.logical_and(y_true_int[:, 0] == y_pred_int[:, 0], y_true_int[:, 1] == y_pred_int[:, 1])
    return tf.cast(result, tf.float32)


### Resolution of 4-momentum:
class MyResolution(tf.keras.metrics.Metric):
    def __init__(self, _name, var_pos, is_relative = False,**kwargs):
        super(MyResolution, self).__init__(name=_name,**kwargs)
        self.is_relative = is_relative
        self.var_pos     = var_pos
        self.sum_x       = self.add_weight(name="sum_x", initializer="zeros")
        self.sum_x2      = self.add_weight(name="sum_x2", initializer="zeros")
        self.N           = self.add_weight(name="N", initializer="zeros")

    def update_state(self, y_true, y_pred, sample_weight=None):
        self.N.assign_add(tf.cast(tf.shape(y_true)[0], dtype=tf.float32))
        if(self.is_relative):
            self.sum_x.assign_add(tf.math.reduce_sum((y_pred[:,self.var_pos]   - y_true[:,self.var_pos])/y_true[:,self.var_pos]))
            self.sum_x2.assign_add(tf.math.reduce_sum(((y_pred[:,self.var_pos] - y_true[:,self.var_pos])/y_true[:,self.var_pos])**2))
        else:
            self.sum_x.assign_add(tf.math.reduce_sum(y_pred[:,self.var_pos]   - y_true[:,self.var_pos]))
            self.sum_x2.assign_add(tf.math.reduce_sum((y_pred[:,self.var_pos] - y_true[:,self.var_pos])**2))

    def result(self):
        # tf.print('\nN: ',self.N)
        # tf.print('Sum_x: ',self.sum_x)
        mean_x  = self.sum_x/self.N
        mean_x2 = self.sum_x2/self.N
        return mean_x2 -  mean_x**2

    def reset(self):
        self.sum_x.assign(0.)
        self.sum_x2.assign(0.)
        self.N.assign(0.)
    
    def get_config(self):
        config = {
            "is_relative": self.is_relative,
            "var_pos": self.var_pos,
            "name": self.name,
        }
        base_config = super(MyResolution, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

    @classmethod
    def from_config(config):
        raise RuntimeError("Im here")
        return MyResolution(config["name"], config["var_pos"], is_relative=config["is_relative"])

pt_res_obj  = MyResolution('pt_res' , 2 ,True)
eta_res_obj = MyResolution('eta_res', 3 ,False)
phi_res_obj = MyResolution('phi_res', 4 ,False)
m2_res_obj  = MyResolution('m^2_res', 5 ,False)

def pt_res(y_true, y_pred, sample_weight=None):
    # print('\npt_res calculation:')
    global pt_res_obj
    pt_res_obj.update_state(y_true, y_pred)
    return pt_res_obj.result()

def eta_res(y_true, y_pred, sample_weight=None):
    global eta_res_obj
    eta_res_obj.update_state(y_true, y_pred)
    return eta_res_obj.result()

def phi_res(y_true, y_pred, sample_weight=None):
    global phi_res_obj
    phi_res_obj.update_state(y_true, y_pred)
    return phi_res_obj.result()

def m2_res(y_true, y_pred, sample_weight=None):
    global m2_res_obj
    m2_res_obj.update_state(y_true, y_pred)
    return m2_res_obj.result()

def decay_mode_histo(x1, x2, dm_bins):
    decay_mode = np.zeros((x1.shape[0],2))
    decay_mode[:,0] = x1
    decay_mode[:,1] = x2
    h_dm, _ = np.histogramdd(decay_mode, bins=[dm_bins,dm_bins])
    h_dm[:,-1] = h_dm[:,4]+h_dm[:,-1] # sum the last and 4. column into the last column
    h_dm = np.delete(h_dm,4,1)        # delete the 4. column
    h_dm[-1,:] = h_dm[4,:]+h_dm[-1,:] # sum the last and 4. column into the last column
    h_dm = np.delete(h_dm,4,0)        # delete the 4. column
    return h_dm

##### Custom loss function:
class CustomMSE(keras.losses.Loss):
    def __init__(self, name="custom_mse",**kwargs):
        super().__init__(name=name,**kwargs)

    def call(self, y_true, y_pred):
        # w = [0.3, 0.14, 0.14, 0.14, 0.14, 0.14]
        # print('\nLoss calculation:')
        w = [1., 1, 1, 1, 1, 1]
        mse1 = tf.math.reduce_mean(tf.square(y_true[:,0] - y_pred[:,0]))
        mse2 = tf.math.reduce_mean(tf.square(y_true[:,1] - y_pred[:,1]))
        mse3 = tf.math.reduce_mean(tf.square(y_true[:,2] - y_pred[:,2]))
        mse4 = tf.math.reduce_mean(tf.square(y_true[:,3] - y_pred[:,3]))
        mse5 = tf.math.reduce_mean(tf.square(y_true[:,4] - y_pred[:,4]))
        mse6 = tf.math.reduce_mean(tf.square(y_true[:,5] - y_pred[:,5]))
        return w[0]*mse1 + w[1]*mse2 + w[2]*mse3 + w[3]*mse4 + w[4]*mse5 + w[5]*mse6


class ValidationCallback(tf.keras.callbacks.Callback):
    def on_epoch_begin(self, epoch, logs=None):
        ### Reset the variables of class MyResolution:
        global pt_res_obj
        global eta_res_obj
        global phi_res_obj
        global m2_res_obj
        pt_res_obj.reset()
        eta_res_obj.reset()
        phi_res_obj.reset()
        m2_res_obj.reset()
        print('Resolution reset done\n')

    def on_epoch_end(self, epoch, logs=None):
        # keys = list(logs.keys())
        # print("Log keys: {}".format(keys))
        print("\nValidation:")
        generator_val, n_batches_val = make_generator('/data/store/reco_skim_v1/tau_DYJetsToLL_M-50.root',entry_start_val, entry_stop_val) 
        myresults = self.model.evaluate(x = tf.data.Dataset.from_generator(generator_val,(tf.float32, tf.float32),\
                            (tf.TensorShape([None,n_pf,n_fe]), tf.TensorShape([None,n_labels]))), batch_size = n_batches_val, steps = n_steps_val)
        if len(self.model.metrics_names) == 1:
            i = self.model.metrics_names[0]
            logs["val_"+i] = myresults
        else:
            cnt = 0
            for i in self.model.metrics_names:
                logs["val_"+i] = myresults[cnt]
                cnt += 1
        # print('Validation finished.')
        ### Save the entire models:
        self.model.save("/data/cedrine/Models0/my_model_{}".format(epoch+1),save_format='tf')
        print('Model is saved.')
         

callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor   = 'val_loss', 
        min_delta = 0, # Minimum change in the monitored quantity to qualify as an improvement
        patience  = 5, # Number of epochs with no improvement after which training will be stopped
        verbose   = 0, 
        mode      = 'min', # it will stop when the quantity monitored has stopped decreasing
        baseline  = None, 
        restore_best_weights = False,
    ),
    tf.keras.callbacks.CSVLogger(
        filename  = '/data/cedrine/Models0/log0.csv', 
        separator = ',', 
        append    = False,
    )
]
