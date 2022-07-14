#!/usr/bin/env python3

# This is a basic webserver that will wrap the emo20q questioner
# agent and implement the dialog by representing user input by http
# request and system response by http response

import pickle # for saving python objects
import os # for paths
import sys  # set the python path to find emo20q module
import time # for sleep
import uuid # for creating a random name for the pickled agent

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
    app.logger.debug("session:%s"%session['sessionid'], extra={"ip": request.remote_addr})
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

    sessionid = session['sessionid']

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
    socketio.run(app, host="0.0.0.0", debug=True)
