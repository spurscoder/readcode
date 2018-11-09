# -*- coding: utf-8 -*-
import numpy as np
import tensorflow as tf
from tensorflow.contrib import rnn
from tensorflow.contrib import layers
from tensorflow.contrib import crf
from tensorflow.contrib import seq2seq
from .supercell import HyperLSTMCell

class DictHyperModel(object):

    def __init__(self,vocab_size,word_dim,hidden_dim,
                 pad_word,init_embedding=None,
                 num_classes=4,clip=5,
                 lr=0.001,l2_reg_lamda=0.0,num_layers=1,
                 rnn_cell='lstm',bi_direction=False,
                 hidden_dim2=128,hyper_embedding_size=16
                 ):

        self.x=tf.placeholder(dtype=tf.int32,shape=[None,None,9],name='input_x')
        self.y=tf.placeholder(dtype=tf.int32,shape=[None,None],name='input_y')
        self.dict=tf.placeholder(dtype=tf.float32,shape=[None,None,8],name='dict')
        self.dropout_keep_prob=tf.placeholder(dtype=tf.float32,name='dropout_keep_prob')
        self.seq_length=tf.reduce_sum(tf.cast(tf.not_equal(self.x[:,:,2], tf.ones_like(self.x[:,:,2])*pad_word), tf.int32), 1)
        self.weights=tf.cast(tf.not_equal(self.x[:,:,2], tf.ones_like(self.x[:,:,2])*pad_word), tf.float32)
        self.batch_size = tf.shape(self.x)[0]

        if init_embedding is None:
            self.embedding=tf.get_variable(shape=[vocab_size,word_dim],dtype=tf.float32,name='embedding')
        else:
            self.embedding=tf.Variable(init_embedding,dtype=tf.float32,name='embedding')

        with tf.variable_scope('embedding'):
            x=tf.nn.embedding_lookup(self.embedding,self.x)
            x = tf.reshape(x, [self.batch_size, -1, 9 * word_dim])

        def lstm_cell(dim):
            cell=rnn.BasicLSTMCell(dim)
            cell=rnn.DropoutWrapper(cell,output_keep_prob=self.dropout_keep_prob)
            return cell

        def hyperlstm_cell(dim):
            cell=HyperLSTMCell(num_units=hidden_dim,forget_bias=1.0,use_recurrent_dropout=False,
                               dropout_keep_prob=1.0,use_layer_norm=False,hyper_num_units=hidden_dim2,
                               hyper_embedding_size=hyper_embedding_size,hyper_use_recurrent_dropout=False)
            cell=rnn.DropoutWrapper(cell,output_keep_prob=self.dropout_keep_prob)
            return cell

        with tf.variable_scope('first_layer'):
            inputx=tf.concat([x,self.dict],axis=2)
            (forward_output,backword_output),_=tf.nn.bidirectional_dynamic_rnn(
                cell_fw=hyperlstm_cell(hidden_dim),
                cell_bw=hyperlstm_cell(hidden_dim),
                inputs=inputx,
                sequence_length=self.seq_length,
                dtype=tf.float32
            )
            output=tf.concat([forward_output,backword_output],axis=2)

        with tf.variable_scope('loss'):

            self.output=layers.fully_connected(
                inputs=output,
                num_outputs=num_classes,
                activation_fn=None,
                )
            #crf
            log_likelihood, self.transition_params = crf.crf_log_likelihood(
                self.output, self.y, self.seq_length)

            loss = tf.reduce_mean(-log_likelihood)

        with tf.variable_scope('train_op'):
            self.optimizer=tf.train.AdamOptimizer(learning_rate=lr)
            tvars=tf.trainable_variables()
            l2_loss = tf.add_n([tf.nn.l2_loss(v) for v in tvars if v.get_shape().ndims > 1])
            self.loss=loss+l2_reg_lamda*l2_loss
            grads,_=tf.clip_by_global_norm(tf.gradients(self.loss,tvars),clip)
            self.train_op=self.optimizer.apply_gradients(zip(grads,tvars))

    def train_step(self,sess,x_batch,x_dict,y_batch,dropout_keep_prob):
        feed_dict={
            self.x:x_batch,
            self.dict:x_dict,
            self.y:y_batch,
            self.dropout_keep_prob:dropout_keep_prob
        }
        _,loss=sess.run([self.train_op,self.loss],feed_dict)
        return loss

    def dev_step(self,sess,x_batch,x_dict,y_batch):
        feed_dict={
            self.x:x_batch,
            self.dict:x_dict,
            self.y:y_batch,
            self.dropout_keep_prob:1.0
        }
        loss,lengths,unary_scores, transition_param=sess.run(
            [self.loss,self.seq_length,self.output, self.transition_params],feed_dict)
        predict=[]
        for unary_score,length in zip(unary_scores,lengths):
            if length==0:
                continue
            viterbi_sequence, _=crf.viterbi_decode(unary_score[:length],transition_param)
            predict.append(viterbi_sequence)
        return loss,predict

    def predict_step(self,sess,x_batch,x_dict):
        feed_dict={
            self.x:x_batch,
            self.dict:x_dict,
            self.dropout_keep_prob:1.0
        }
        lengths,unary_scores, transition_param=sess.run(
            [self.seq_length,self.output, self.transition_params],feed_dict)
        predict=[]
        for unary_score,length in zip(unary_scores,lengths):
            if length==0:
                continue
            viterbi_sequence, _=crf.viterbi_decode(unary_score[:length],transition_param)
            predict.append(viterbi_sequence)
        return predict



if __name__ == '__main__':
    pass




