#!/usr/bin/env python3

# This is a basic webserver that will wrap the emo20q questioner
# agent and implement the dialog by representing user input by http
# request and system response by http response

import pickle # for saving python objects
import os # for paths
import sys  # set the python path to find emo20q module
import time # for sleep
import uuid # for creating a random name for the pickled agent

# for tensorflow/bert
import numpy as np
import tensorflow as tf
# !pip install -q tf-models-official==2.4.0
from official.nlp import bert
import official.nlp.bert.tokenization


from gevent import monkey
monkey.patch_all()

# import the web application factory class and instantiate it
from flask import Flask
print(__name__)
app = Flask(__name__)
app.config['SECRET_KEY'] = "don't use this in prod"

# import flask session for cookies
from flask import session

# for static files (todo: for performance, these should be served by
# the webserver
from flask import send_from_directory

# import request for getting query params from user response
from  flask import request

# templates
from flask import render_template

# model setup

gs_folder_bert = "gs://cloud-tpu-checkpoints/bert/v3/uncased_L-12_H-768_A-12"
tf.io.gfile.listdir(gs_folder_bert)
# Set up tokenizer to generate Tensorflow dataset
tokenizer = bert.tokenization.FullTokenizer(
    vocab_file=os.path.join(gs_folder_bert, "vocab.txt"),
     do_lower_case=True)

# print("Vocab size:", len(tokenizer.vocab))

#export_dir = "/home/ec2-user/saved_model_bert_emo20qa"
export_dir = "/Users/kaze7539/Downloads/saved_model_bert_emo20qa"
model  = tf.saved_model.load(export_dir)

lab2id = {"no":0, "maybe":1, "yes":2}
id2lab = {v:k for k,v in lab2id.items()}

def encode_sentence2(s):
   tokens = list(tokenizer.tokenize(s))
   tokens.append('[SEP]')
   return tokenizer.convert_tokens_to_ids(tokens)

def bert_encode2(data_dict):
  num_examples = len(data_dict["emotion"])
  
  sentence1 = tf.ragged.constant([
      encode_sentence2(s)
      for s in np.array(data_dict["emotion"])])
  sentence2 = tf.ragged.constant([
      encode_sentence2(s)
       for s in np.array(data_dict["question"])])

  cls = [tokenizer.convert_tokens_to_ids(['[CLS]'])]*sentence1.shape[0]
  input_word_ids = tf.concat([cls, sentence1, sentence2], axis=-1)

  input_mask = tf.ones_like(input_word_ids).to_tensor()

  type_cls = tf.zeros_like(cls)
  type_s1 = tf.zeros_like(sentence1)
  type_s2 = tf.ones_like(sentence2)
  input_type_ids = tf.concat(
      [type_cls, type_s1, type_s2], axis=-1).to_tensor()

  inputs = {
      'input_word_ids': input_word_ids.to_tensor(),
      'input_mask': input_mask,
      'input_type_ids': input_type_ids}

  return inputs


@app.route('/', methods=['GET'])
def root():
    """given paramemters q, a question, and e, an emotion, return
    yes/no/maybe to aswer the question"""
    
    # we will assume that if the page is reloaded, that the user
    # intends to start a new game so we'll remove the session info
    page = """
    <html>
    <head>
    <title> testing for emo20q qa </title>
    </head>
    <h1> testing for emo20q qa </h1>
    <form>
    <label for="emotion">emotion:</label>
    <input type="text" name="emotion" id="emotion"><br>
    <label for="question">question:</label>
    <input type="text" name="question" id="question"><br>
    <button type="submit" action="/qa">Answer</button>
    </form>
    </html>
    """
    #return render_template('emo20q_chat.html')
    return page

@app.route('/qa', methods=['GET'])
def qa():
    """given paramemters q, a question, and e, an emotion, return
    yes/no/maybe to aswer the question"""
    
    # we will assume that if the page is reloaded, that the user
    # intends to start a new game so we'll remove the session info

    # if no args, then return the default page
    
    page = """
    <html>
    <head>
    <title> testing for emo20q qa </title>
    </head>
    <h1> testing for emo20q qa </h1>
    
    <h2> enter an emotion and a question below <h2>
    
    <form>
    <label for="emotion">emotion:</label>
    <input type="text" name="emotion" id="emotion"><br>
    <label for="question">question:</label>
    <input type="text" name="question" id="question"><br>
    <button type="submit" action="/qa">Answer</button>
    </form>
    </html>
    """
    args = request.args
    emotion = args.get("emotion")
    question = args.get("question")

    if emotion is None or question is None:
        return page

    # if there are args, run them through bert
    
    encoded = bert_encode2({"emotion": [emotion], "question": [question]})
    #print(emotion,question, encoded)
    res = model([encoded['input_word_ids'],
                 encoded['input_mask'],
                 encoded['input_type_ids']], training=False)
    #print(res)
    # print(tf.argmax(res, axis=1))
    # print(tf.argmax(res, axis=1)[0])
    # print(id2lab[int(tf.argmax(res, axis=1)[0])])
    answer = id2lab[int(tf.argmax(res, axis=1)[0])]
    #return render_template('emo20q_chat.html')
    return f"""
    <html>
    <head>
    <title> testing for emo20q qa </title>
    </head>
    <h1> testing for emo20q qa </h1>
    
    <h3> emotion: {emotion} </h3>
    <h3> question: {question} </h3>
    <h2> answer: {answer} </h2>
    <form>
    <label for="emotion">emotion:</label>
    <input type="text" name="emotion" id="emotion"><br>
    <label for="question">question:</label>
    <input type="text" name="question" id="question"><br>
    <button type="submit" action="/qa">Answer</button>
    </form>
    </html>

    """


@app.route("/get_my_ip", methods=["GET"])
def get_my_ip():
    return request.remote_addr

if __name__ == '__main__':
    app.run(debug=True)
