# -*- coding: utf-8 -*-
"""chatbot_v8.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/VGGatGitHub/AnswerFlow/blob/master/chatbot_v8.ipynb

https://www.kaggle.com/datasets?search=nq-train

V2: added comads to look at the structure of the train.json file and to assess the %s.

V3: changing the code to do tarining for long_answesrs or short_answers using training_for_long_answer switch.

V4: reading in json file produced from jsonl using jsonl2json.ipynb

V6: reading files from GitHub

V7: using similarity function to assess the new answers 

V8: modified the geting of the training data file
"""

# Commented out IPython magic to ensure Python compatibility.
from __future__ import absolute_import, division, print_function, unicode_literals

#VGG in case of using a Google Drive for your files
#from google.colab import drive
#drive.mount('/content/drive')
#path='/content/drive/My Drive/Colab Notebooks/'

import sys 
import os
print(os.getcwd())

#VGG define the foldre to inspect for files 
path=os.getcwd()+"/"

#VGG read in training data
#you may have to adjust the BATCH_SIZE acordingly 
#path='/content/drive/My Drive/Colab Notebooks/'

file_name='train200.json' #or train25.json or train200.json 

file_to_read=path+file_name

#Geting the training data file 

from pathlib import Path
import requests

try:
  if not Path(file_to_read).is_file():
    file_url='https://raw.githubusercontent.com/VGGatGitHub/natural-questions/master/'+file_name
    print("Will try to fetch the file from:\n",file_url)

    response = requests.get(file_url)
    if response.status_code == 200:
      print('Success!')
      s=response.content
      # Code for printing to a file 
      sample = open(file_to_read, 'w') 
      doc=s.decode()
      print(doc, file = sample) 
      sample.close()
    else:
      print("Faild to fetch the file!\n",file_url)
      print(response)
except Exception:
    print("Exception: Faild to find or fetch the training file needed:",file_name)

#make sure the file you what is in the correct directory
#some possible files are train.json or train200.json 

for dirname, _, filenames in os.walk(path):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# VGG
# you may need to get the file text_utils.py from 
# https://github.com/VGGatGitHub/natural-questions
#

# sys.path.append(os.path.abspath(path))
# from text_utils import *

# got import errors on colab using import code above
# import text_utils

#VGG The cell has been removed since now the data is analized in the jsonl2json.ipynb


# Install TensorFlow
try:
  # %tensorflow_version only exists in Colab.
  # %tensorflow_version 2.x
  print("TensorFlow 2.x is needed!")
except Exception:
    pass

import tensorflow as tf
print(tf.__version__)

#from __future__ import absolute_import, division, print_function, unicode_literals

import tensorflow as tf

from sklearn.model_selection import train_test_split

import unicodedata
import re
import numpy as np
import os
import io
import time
import json

# Converts the unicode file to ascii
def unicode_to_ascii(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn')


def preprocess_sentence(w):
    w = unicode_to_ascii(w.lower().strip())

    # creating a space between a word and the punctuation following it
    # eg: "he is a boy." => "he is a boy ."
    # Reference:- https://stackoverflow.com/questions/3645931/python-padding-punctuation-with-white-spaces-keeping-punctuation
    w = re.sub(r"([?.!,¿])", r" \1 ", w)
    w = re.sub(r'[" "]+', " ", w)

    # replacing everything with space except (0-9, a-z, A-Z, ".", "?", "!", ",")
    w = re.sub(r"[^0-9a-zA-Z?.!,¿]+", " ", w)

    w = w.rstrip().strip()

    # adding a start and an end token to the sentence
    # so that the model know when to start and stop predicting.
    w = '<start> ' + w + ' <end>'
    return w

#VGG make sure the file_to_read has been defined above! 

UNKNOWN = "<UNKNOWN>"
# 1. Remove the accents
# 2. Clean the sentences
# 3. Return word pairs in the format: [ENGLISH, SPANISH]
def create_dataset():
    source = []
    target = []
    context = []

    n_short_answers=0 #VGG
    n_long=0
    
    training_for_long_answer = False #True #False 
    #make sure to run furst for shor answers and then for long...

    with open(file_to_read) as json_file: #VGG
        data = json.load(json_file)

        for nq_doc in data:
            if filename == 'train200L.json':
              doc = simplify_nq_example(nq_doc) #VGG for jsonl formated file
            else:
              doc=nq_doc

            question_text = doc['question_text']
            document_text = doc['document_text'].split()
            long_answer_candidates = doc['long_answer_candidates']
            annotations = doc['annotations'][0]
            
            if annotations['long_answer']['start_token'] < annotations['long_answer']['end_token']:
                
                n_long+=1
                long_answer = " ".join(document_text[annotations['long_answer']['start_token']:
                                                     annotations['long_answer']['end_token']])
                                      
                if len(annotations['short_answers']) > 0:
                    start_token = annotations['short_answers'][0]['start_token']
                    end_token = annotations['short_answers'][0]['end_token']
                    short_answer = " ".join(document_text[start_token:end_token])
                    n_short_answers+=1 #VGG
                else:
                    short_answer = UNKNOWN
                
                #VGG V3
                if training_for_long_answer :
                    short_answer=long_answer #VGG V3 change - make the target to be the long answer instead of the short answer 
                    for posibilities in long_answer_candidates:
                        if posibilities["top_level"]:
                            start_token = posibilities['start_token']
                            end_token = posibilities['end_token']                    
                            posibility = " ".join(document_text[start_token:end_token])
                            context.append(preprocess_sentence(posibility))
                else:
                    context.append(preprocess_sentence(long_answer))
                #VGG context = [] #VGG it seems to work better!

                source.append(preprocess_sentence(question_text))
                target.append(preprocess_sentence(short_answer))
#VGG                
        print("Data set of:",len(data)," elements. It contains:",
              n_short_answers,"short answers out of", n_long,
              "possible long answers, short/long rate is {:.0f}%".format(
                  100*n_short_answers/n_long))    
    return target, source, context

def max_length(tensor):
    return max(len(t) for t in tensor)
    
def tokenize(lang):
  lang_tokenizer = tf.keras.preprocessing.text.Tokenizer(
      filters='')
  lang_tokenizer.fit_on_texts(lang)
  tensor = lang_tokenizer.texts_to_sequences(lang)
  tensor = tf.keras.preprocessing.sequence.pad_sequences(tensor,
                                                         padding='post')
  return tensor, lang_tokenizer

def load_dataset():
    # creating cleaned input, output pairs
    targ_lang, inp_lang, context_lang = create_dataset()

    input_tensor, inp_lang_tokenizer = tokenize(inp_lang)
    target_tensor, targ_lang_tokenizer = tokenize(targ_lang)
    
    return input_tensor, target_tensor, inp_lang_tokenizer, targ_lang_tokenizer

def convert(lang, tensor):
  for t in tensor:
    if t!=0:
      print ("%d ----> %s" % (t, lang.index_word[t]))

class Encoder(tf.keras.Model):
  def __init__(self, vocab_size, embedding_dim, enc_units, batch_sz):
    super(Encoder, self).__init__()
    self.batch_sz = batch_sz
    self.enc_units = enc_units
    self.embedding = tf.keras.layers.Embedding(vocab_size, embedding_dim)
    self.gru = tf.keras.layers.GRU(self.enc_units,
                                   return_sequences=True,
                                   return_state=True,
                                   recurrent_initializer='glorot_uniform')

  def call(self, x, hidden):
    x = self.embedding(x)
    output, state = self.gru(x, initial_state = hidden)
    return output, state

  def initialize_hidden_state(self):
    return tf.zeros((self.batch_sz, self.enc_units))
    
class BahdanauAttention(tf.keras.layers.Layer):
  def __init__(self, units):
    super(BahdanauAttention, self).__init__()
    self.W1 = tf.keras.layers.Dense(units)
    self.W2 = tf.keras.layers.Dense(units)
    self.V = tf.keras.layers.Dense(1)

  def call(self, query, values):
    # hidden shape == (batch_size, hidden size)
    # hidden_with_time_axis shape == (batch_size, 1, hidden size)
    # we are doing this to perform addition to calculate the score
    hidden_with_time_axis = tf.expand_dims(query, 1)

    # score shape == (batch_size, max_length, 1)
    # we get 1 at the last axis because we are applying score to self.V
    # the shape of the tensor before applying self.V is (batch_size, max_length, units)
    score = self.V(tf.nn.tanh(
        self.W1(values) + self.W2(hidden_with_time_axis)))

    # attention_weights shape == (batch_size, max_length, 1)
    attention_weights = tf.nn.softmax(score, axis=1)

    # context_vector shape after sum == (batch_size, hidden_size)
    context_vector = attention_weights * values
    context_vector = tf.reduce_sum(context_vector, axis=1)

    return context_vector, attention_weights
    
class Decoder(tf.keras.Model):
  def __init__(self, vocab_size, embedding_dim, dec_units, batch_sz):
    super(Decoder, self).__init__()
    self.batch_sz = batch_sz
    self.dec_units = dec_units
    self.embedding = tf.keras.layers.Embedding(vocab_size, embedding_dim)
    self.gru = tf.keras.layers.GRU(self.dec_units,
                                   return_sequences=True,
                                   return_state=True,
                                   recurrent_initializer='glorot_uniform')
    self.fc = tf.keras.layers.Dense(vocab_size)

    # used for attention
    self.attention = BahdanauAttention(self.dec_units)

  def call(self, x, hidden, enc_output):
    # enc_output shape == (batch_size, max_length, hidden_size)
    context_vector, attention_weights = self.attention(hidden, enc_output)

    # x shape after passing through embedding == (batch_size, 1, embedding_dim)
    x = self.embedding(x)

    # x shape after concatenation == (batch_size, 1, embedding_dim + hidden_size)
    x = tf.concat([tf.expand_dims(context_vector, 1), x], axis=-1)

    # passing the concatenated vector to the GRU
    output, state = self.gru(x)

    # output shape == (batch_size * 1, hidden_size)
    output = tf.reshape(output, (-1, output.shape[2]))

    # output shape == (batch_size, vocab)
    x = self.fc(output)

    return x, state, attention_weights

# Try experimenting with the size of that dataset
input_tensor, target_tensor, inp_lang, targ_lang = load_dataset()

# Calculate max_length of the target tensors
max_length_targ, max_length_inp = max_length(target_tensor), max_length(input_tensor)    

# Creating training and validation sets using an 80-20 split
input_tensor_train, input_tensor_val, target_tensor_train, target_tensor_val = train_test_split(input_tensor, target_tensor, test_size=0.2)

BUFFER_SIZE = len(input_tensor_train)
BATCH_SIZE = 1 #VGG
steps_per_epoch = len(input_tensor_train)//BATCH_SIZE
embedding_dim = 512
units = 1024
vocab_inp_size = len(inp_lang.word_index)+1
vocab_tar_size = len(targ_lang.word_index)+1

dataset = tf.data.Dataset.from_tensor_slices((input_tensor_train, target_tensor_train)).shuffle(BUFFER_SIZE)
dataset = dataset.batch(BATCH_SIZE, drop_remainder=True)

example_input_batch, example_target_batch = next(iter(dataset))
example_input_batch.shape, example_target_batch.shape

encoder = Encoder(vocab_inp_size, embedding_dim, units, BATCH_SIZE)    
decoder = Decoder(vocab_tar_size, embedding_dim, units, BATCH_SIZE)
optimizer = tf.keras.optimizers.Adam()
loss_object = tf.keras.losses.SparseCategoricalCrossentropy(
    from_logits=True, reduction='none')
    
def loss_function(real, pred):
  mask = tf.math.logical_not(tf.math.equal(real, 0))
  loss_ = loss_object(real, pred)
  mask = tf.cast(mask, dtype=loss_.dtype)
  loss_ = tf.multiply(loss_, mask)
  return tf.reduce_mean(loss_)


#VGG uncommented for possible checkpoint saving later 

checkpoint_dir = './training_checkpoints'
checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
checkpoint = tf.train.Checkpoint(optimizer=optimizer,
                                 encoder=encoder,
                                 decoder=decoder)  

                                 
@tf.function
def train_step(inp, targ, enc_hidden):
  loss = 0

  with tf.GradientTape() as tape:
    enc_output, enc_hidden = encoder(inp, enc_hidden)
    dec_hidden = enc_hidden
    dec_input = tf.expand_dims([targ_lang.word_index['<start>']] * BATCH_SIZE, 1)

    # Teacher forcing - feeding the target as the next input
    for t in range(1, targ.shape[1]):
      # passing enc_output to the decoder
      predictions, dec_hidden, _ = decoder(dec_input, dec_hidden, enc_output)

      loss += loss_function(targ[:, t], predictions)

      # using teacher forcing
      dec_input = tf.expand_dims(targ[:, t], 1)

  batch_loss = (loss / int(targ.shape[1]))
  variables = encoder.trainable_variables + decoder.trainable_variables
  gradients = tape.gradient(loss, variables)
  optimizer.apply_gradients(zip(gradients, variables))
  return batch_loss
  
def evaluate(sentence):
    attention_plot = np.zeros((max_length_targ, max_length_inp))
    sentence = preprocess_sentence(sentence)

    inputs = [inp_lang.word_index.get(i, 0) for i in sentence.split(' ')]
    inputs = tf.keras.preprocessing.sequence.pad_sequences([inputs],
                                                           maxlen=max_length_inp,
                                                           padding='post')
    inputs = tf.convert_to_tensor(inputs)

    result = ''
    hidden = [tf.zeros((1, units))]
    enc_out, enc_hidden = encoder(inputs, hidden)

    dec_hidden = enc_hidden
    dec_input = tf.expand_dims([targ_lang.word_index['<start>']], 0)

    result ='<start> '#VGG 
    for t in range(max_length_targ):
        predictions, dec_hidden, attention_weights = decoder(dec_input,
                                                             dec_hidden,
                                                             enc_out)

        # storing the attention weights to plot later on
        attention_weights = tf.reshape(attention_weights, (-1, ))
        attention_plot[t] = attention_weights.numpy()

        predicted_id = tf.argmax(predictions[0]).numpy()
        result += targ_lang.index_word[predicted_id] + ' '

        if targ_lang.index_word[predicted_id] == '<end>':
            return result, sentence, attention_plot

        # the predicted ID is fed back into the model
        dec_input = tf.expand_dims([predicted_id], 0)
    return result, sentence, attention_plot
    
#If you get error message about iretation problem -  check your BATCH_SIZE

EPOCHS = 100

epoch=-1
total_loss=1
total_loss_cut=0.001*steps_per_epoch*BATCH_SIZE
training_start_time=time.time()

print("\nStarting training of at most {} epochs or until total loss is les than {:0.4f}".format(EPOCHS,total_loss_cut))
while (epoch < EPOCHS) and (total_loss > total_loss_cut):
  epoch+=1

  start = time.time()
  enc_hidden = encoder.initialize_hidden_state()
  total_loss = 0

  for (batch, (inp, targ)) in enumerate(dataset.take(steps_per_epoch)):
    batch_loss = train_step(inp, targ, enc_hidden)
    total_loss += batch_loss

    if batch%8 == 0:
      print('Epoch {} Batch {} Loss {:.4f}'.format(epoch + 1,
                                                     batch,
                                                     batch_loss.numpy()))
  '''
  # saving (checkpoint) the model every 2 epochs
  if (epoch + 1) % 2 == 0:
    checkpoint.save(file_prefix = checkpoint_prefix)
  '''   

  print('Epoch {} Total Loss {:.4f}'.format(epoch + 1, total_loss))
  print('Time taken for this epoch {:.4f} sec\n'.format(time.time() - start))

print('BATCH_SIZE:{}, total training time {:.2f} minutes for {} epochs, final total_loss {:.4f}\n'.format(
    BATCH_SIZE,(time.time() - training_start_time)/60,epoch+1,total_loss))

print('BATCH_SIZE:{}, total training time {:.2f} minutes for {} epochs, final total_loss {:.4f}\n'.format(
    BATCH_SIZE,(time.time() - training_start_time)/60,epoch+1,total_loss))

# function for plotting the attention weights
try:
  
  import matplotlib.pyplot as plt
  import matplotlib.ticker as ticker

  def plot_attention(attention, sentence, predicted_sentence):
      fig = plt.figure(figsize=(10,10))
      ax = fig.add_subplot(1, 1, 1)
      ax.matshow(attention, cmap='viridis')
      fontdict = {'fontsize': 14}
      ax.set_xticklabels([''] + sentence, fontdict=fontdict, rotation=90)
      ax.set_yticklabels([''] + predicted_sentence, fontdict=fontdict)
      ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
      ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
      plt.show()
      
  def show_attention_plot(sentence):
      result, sentence1, attention_plot = evaluate(sentence)
      attention_plot = attention_plot[:len(result.split(' ')), :len(sentence.split(' '))]
      plot_attention(attention_plot, sentence.split(' '), result.split(' '))
      
except Exception:
  pass



def ask(sentence):
    result, sentence1, attention_plot = evaluate(sentence)
    print('\nQuestion: %s' % (sentence))
    print('Predicted answer: {}'.format(result))
    return result


def is_it_known(sentence):
    result, sentence, attention_plot = evaluate(sentence)
    if result.split() != ['<start>', 'unknown', '<end>']: return True
    return False

ask('which is the most common use of opt-in e-mail marketing')    
ask('most common use of opt-in e-mail marketing')
ask('how did I meet your mother')
ask('who is your mother');

try:
  show_attention_plot("which is the most common use of opt in e mail marketing")
  show_attention_plot("who plays young flo in the progressive commercials")
except Exception:
  pass


try:
  import spacy.cli
  spacy.cli.download("en_core_web_md")
except Exception:
    print("try to do sudo python3 -m spacy download en_core_web_md")

import spacy as sp
nlp = sp.load("en_core_web_md")

# Test the similarity measure and get some idea about the output values 

# sample text
messages = [
# Smartphones
"My phone is not good.",
"Your cellphone looks great.",
# Weather
"Will it snow tomorrow?",
"Recently a lot of hurricanes have hit the US",
# Food and health
"An apple a day, keeps the doctors away",
"Eating strawberries is healthy"
]

for text1 in messages:
  doc1 = nlp(text1)
  print()
  for text2 in messages:
    doc2 = nlp(text2)
    print(doc1.similarity(doc2))

target, source, context = create_dataset()

print("\ngoing over all the questions and selecting those with answers ... \n")

n_answers=0
i=-1
n_correct=0
n_smlr=0
smlrty_cut=85
for question_text in source:
    i+=1
    TheAnswer=target[i]
    TheAnswer=TheAnswer.replace('<start>',' ')
    TheAnswer=TheAnswer.replace('<end>',' ')
    doc1 = nlp(TheAnswer)
    if is_it_known(question_text):
        n_answers+=1
        AFanswer=ask(question_text)
        AFanswer=AFanswer.replace('<start>',' ')
        AFanswer=AFanswer.replace('<end>',' ')
        doc2 = nlp(AFanswer)
        if AFanswer.split() == TheAnswer.split(): 
          n_correct+=1
        else:
          smlrty=100*doc1.similarity(doc2)
          if smlrty > smlrty_cut: n_smlr+=1
          print("The answer was:",target[i])
          print("Similarity:{:0.2f}%\n".format(smlrty))

print("\n{} answers out of {} possible, rate is {:.0f}%".format(n_answers,len(source),100*n_answers/len(source)))
if n_answers >0:
  print("At least {} correct answers out of {} possible, rate is {:.0f}%".format(n_correct,n_answers,100*n_correct/n_answers))
if n_smlr >0:
  print("There were {} similar answers with  similarity above {}%\n".format(n_smlr,smlrty_cut))

target, source, context = create_dataset()

print("Short Answer training results:")
print("\n{} answers out of {} possible, rate is {:.0f}%".format(n_answers,len(source),100*n_answers/len(source)))
if n_answers >0:
  print("At least {} correct answers out of {} possible, rate is {:.0f}%".format(n_correct,n_answers,100*n_correct/n_answers))
if n_smlr >0:
  print("There were {} similar answers with  similarity above {}%\n".format(n_smlr,smlrty_cut))

#print("Long Answer training results:")
print("\n{} answers out of {} possible, rate is {:.0f}%".format(n_answers,len(source),100*n_answers/len(source)))
if n_answers >0:
  print("At least {} correct answers out of {} possible, rate is {:.0f}%".format(n_correct,n_answers,100*n_correct/n_answers))
if n_smlr >0:
  print("There were {} similar answers with  similarity above {}%\n".format(n_smlr,smlrty_cut))
