#!/usr/bin/env python3

# This is a basic webserver that will wrap the emo20q questioner
# agent and implement the dialog by representing user input by http
# request and system response by http response

import pickle # for saving python objects
import os # for paths
import sys  # set the python path to find emo20q module
import uuid # for creating a random name for the pickled agent

# import the web application factory class and instantiate it
from flask import Flask
print(__name__)
app = Flask(__name__)

# import flask session for cookies
from flask import session

# import request for getting query params from user response
from  flask import request

# templates
from flask import render_template




# import emo20q agent: need to set the path
path = "./emo20q"
if path not in sys.path:
    sys.path.insert(0,path)
sys.path.insert(0,path)
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
def chat():
    """this is the main function of the app

    first, we'll load the agent.  Either this will be a new agent (if
    there is no session/cookie or if there is an error) or this will
    be a pickled agent from the previous turn

    Then we'll process any user input

    Then we'll render the page: the previous turns and a textbox

    Then we'll pickle the agent

    Then we'll return the response"""

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


    # is there any user input?
    user_input = request.args.get("user_input", "")
    print(user_input)
    # give the user input to the agent
    agent_output = agent(user_input)
    print(agent_output)

    # pickle the agent
    pickle.dump([agent.episodicBuffer, agent.state.name,
                 agent.belief], open(pickled_path, "wb"))

    #return('Agent says: ' + agent_output)
    return render_template('template.html', agent_output=agent_output)

if __name__ == '__main__':
    app.config['SECRET_KEY'] = "don't use this in prod"
    app.run(debug=True)
