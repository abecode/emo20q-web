#!/usr/bin/env python3

# This is a basic webserver that will wrap the emo20q questioner
# agent and implement the dialog by representing user input by http
# request and system response by http response

import pickle # for saving python objects
import os # for paths
import sys  # set the python path to find emo20q module
import time # for sleep
import uuid # for creating a random name for the pickled agent

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

# socket.io
from flask_socketio import SocketIO, emit
socketio = SocketIO(app, logger=True, engineio_logger=True)


# for tensorflow/bert
import numpy as np
import tensorflow as tf
# !pip install -q tf-models-official==2.4.0
from official.nlp import bert
import official.nlp.bert.tokenization

# Set up tokenizer to generate Tensorflow dataset
tokenizer = bert.tokenization.FullTokenizer(
   #vocab_file=os.path.join(gs_folder_bert, "vocab.txt"),
   vocab_file="vocab.txt",
     do_lower_case=True)
export_dir = "/home/ec2-user/saved_model_bert_emo20qa"
#export_dir = "/Users/kaze7539/Downloads/saved_model_bert_emo20qa"
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


# import emo20q agent: need to set the path
path = "./emo20q"
if path not in sys.path:
    sys.path.insert(0,path)
sys.path.insert(0,path)

import emo20q
from emo20q.gpdaquestioner import QuestionerAgent

# it would be nice to just pickle the whole agent, but because of
# lambdas we need to reconstruct the agent from episodic buffer (short
# term memory) and lexical access (word knowledge)
from emo20q.gpdaquestioner import LexicalAccess
from emo20q.gpdaquestioner import SemanticKnowledge
from emo20q.gpdaquestioner import EpisodicBuffer

# create an endpoint/route for the app ( '/' is the root of the
# server)
@app.route('/')
def index():
    """ the main webpage """
    #session['sessionid'] = uuid.uuid4()
    #session['ip'] = request.remote

    # we will assume that if the page is reloaded, that the user
    # intends to start a new game so we'll remove the session info
    if 'agent_id' in session:
        del session['agent_id']
    app.logger.debug("new session", extra={"ip": request.remote_addr})
    return render_template('emo20q_chat.html')

@app.route('/css/<path:filename>')
def css(filename):
    """ to get css """
    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "css"))
    print(directory)
    return send_from_directory(directory, filename)

@app.route('/img/<path:filename>')
def img(filename):
    """ images """
    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "img"))
    return send_from_directory(directory, filename)

# socket connection events
@socketio.on('connect', namespace='/pbot')
def pbot_connect():
    """ first connection where the dialog system starts"""

    # create agent
    # first get agent file name if it exists
    if 'agent_id' in session: # if the user has already visited
        agent_id = session['agent_id']
    else:
        agent_id = uuid.uuid4()
        print(agent_id)
        session['agent_id'] = agent_id

    # try top open and load the pickled agent
    pickled_path = str(agent_id)
    print(pickled_path)
    if os.path.exists(pickled_path):
        try:
            """ this part is a bit verbose and error prone"""
            episodic_buffer, state_name, belief = \
                    pickle.load(open(str(pickled_path), "rb"))
            agent = QuestionerAgent(episodicBuffer=episodic_buffer,
                                    lexicalAccess=LexicalAccess(),
                                    semanticKnowledge=SemanticKnowledge())
            #import pdb; pdb.set_trace()
            agent.set_state(getattr(agent, state_name))
            agent.belief = belief
        except Exception as ex: # normally a bare except is not good but this is just
                # for illustration
            print(ex)
            agent = QuestionerAgent()
    else: # this should occur when it is the users first visit
        agent = QuestionerAgent()


    #time.sleep(1)
    emit('loguser', {'data': '[user enters]'})
    time.sleep(1)

    # give the user input to the agent, start with just empty to start
    try:
        agent_output = agent("")
    except emo20q.gpda.GPDAError: # if there's an error, reset the session
        del session['agent_id']
        agent_id = uuid.uuid4()
        print(agent_id)
        session['agent_id'] = agent_id
        agent = QuestionerAgent()
        agent_output = agent("")

    print(agent_output)

    # pickle the agent
    pickle.dump([agent.episodicBuffer, agent.state.name,
                 agent.belief], open(pickled_path, "wb"))

    #return('Agent says: ' + agent_output)
    for line in agent_output.strip().split("\n"):
        time.sleep(1)
        emit('logagent', {'data': "%s" % line})


    # emit('logagent', {'data': '[emo20q agent enters the universe of discourse]'})
    # time.sleep(1)
    # emit('logagent', {'data': 'Hi I\'m the Emotion Twenty Questions Agent.'})
    # time.sleep(1)
    # emit('logagent', {'data': 'In the game of emotion twenty questions (EMO20Q), you will pick an emotion, then I\'ll try to guess it.'})
    # time.sleep(1)
    # emit('logagent', {'data': 'I\'m not a real person, but you can talk to me like you would talk to a normal person.  Let me know when you have picked an emotion word and are ready to start!'})
    #time.sleep(1)

    #sessionid = session['sessionid']

# socket message events
@socketio.on('UserUtt', namespace='/pbot')
def pbot_message(message):
    """When the user enters input, echo UserUtt as confirmation and
    display on client/browser

    """
    user_input = message['data']
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('loguser',
         {'data':"%s" % user_input})

    # create agent
    # first get agent file name if it exists
    if 'agent_id' in session: # if the user has already visited
        agent_id = session['agent_id']
    else:
        agent_id = uuid.uuid4()
        print(agent_id)
        session['agent_id'] = agent_id

    # try top open and load the pickled agent
    pickled_path = str(agent_id)
    print(pickled_path)
    if os.path.exists(pickled_path):
        try:
            """ this part is a bit verbose and error prone"""
            episodic_buffer, state_name, belief = \
                    pickle.load(open(str(pickled_path), "rb"))
            agent = QuestionerAgent(episodicBuffer=episodic_buffer,
                                    lexicalAccess=LexicalAccess(),
                                    semanticKnowledge=SemanticKnowledge())
            #import pdb; pdb.set_trace()
            agent.set_state(getattr(agent, state_name))
            agent.belief = belief
        except Exception as ex: # normally a bare except is not good but this is just
                # for illustration
            print(ex)
            agent = QuestionerAgent()
    else: # this should occur when it is the users first visit
        agent = QuestionerAgent()


    # give the user input to the agent
    try:
        agent_output = agent(user_input)
    except emo20q.gpda.GPDAError:
        agent_output = ("You can close the window/tab now.\n"
                        "If you want to play again, please refresh the page.")

    print(agent_output)

    # pickle the agent
    pickle.dump([agent.episodicBuffer, agent.state.name,
                 agent.belief], open(pickled_path, "wb"))

    #return('Agent says: ' + agent_output)
    for line in agent_output.strip().split("\n"):
        time.sleep(1)
        emit('logagent', {'data': "%s" % line})


@socketio.on('disconnect', namespace='/pbot')
def pbot_disconnect():
    session.clear()

@app.route("/get_my_ip", methods=["GET"])
def get_my_ip():
    return request.remote_addr

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0",
                 #debug=True,
                 port=5000)
