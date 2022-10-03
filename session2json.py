#!/usr/bin/env python3


import json
#import os
import pickle
import sys

# add emo20q to path
path = "./emo20q"
if path not in sys.path:
    sys.path.insert(0, path)

import emo20q
#from emo20q.gpdaquestioner import QuestionerAgent
from emo20q.qaagent import QAAgent
# it would be nice to just pickle the whole agent, but because of
# lambdas we need to reconstruct the agent from episodic buffer (short
# term memory) and lexical access (word knowledge)
from emo20q.gpdaquestioner import LexicalAccess
from emo20q.gpdaquestioner import SemanticKnowledge
from emo20q.gpdaquestioner import EpisodicBuffer
#from emo20q.qa import answer_emotion_question
from emo20q.episodicbufferqa import AgentAskingTurn
from emo20q.episodicbufferqa import IllocutionaryAct

def get_agent_from_session(sesh):
    #with open(os.path.join(session_dir, sesh), "rb") as f:
    with open(sesh, "rb") as f:    
        episodic_buffer, state_name, belief = pickle.load(f)
        agent = QAAgent(episodicBuffer=episodic_buffer,
                        lexicalAccess=LexicalAccess(),
                        semanticKnowledge=SemanticKnowledge())
    return agent

def print_turns(agent):
    for t in agent.episodicBuffer:
        if isinstance(t, AgentAskingTurn):
            print(t) #print(t.q, t.a)
        elif isinstance(t, IllocutionaryAct):
            print(t)
        else:
            print(t) #(t.gloss, t.semantics, t.talker, t.text)
        print()

def extract_json(agent):        
    """ make the json something like this:
{
  "type": "Dialog",
  "params": {
    "emo20q-commit": "xyz",
    "emo20q-web-commit": "xyz",
    "timestamp": "date-time",
    "sessionfilename": "",
  }
  "container": [
    { "type": "Utterance",
      "text": "agent enters",
      "gloss": null,
      "is_agent": true},
    { "type": "Utterance",
      "text": "ready",
      "gloss": null,
      "is_agent": false},
    { "type": "AgentAskingTurn",
      "container": [
      { "type": "Utterance",
        "text": "is it ...?",
        "gloss": "e=...",
        "is_agent": true}
      { "type": "Utterance",
        "text": "yes",
        "gloss": null,
        "is_agent": false},
      ]
    },
    {"type": "Utterance",
     'text': 'Dammit, that is disappointing... \nWell, what was the emotion that you picked?',
     'gloss': 'fail,ask-emotion',
     'is_agent': True},
    { "type" "Utterance",
      'text': 'irritation',
      'gloss': None,
      'is_agent': False},
    # ...
    # note, the new user asking dialog is not as well structured into "turns"
    { "type": Utterance,
      'text': "Now let's switch roles.  I'll pick the emotion and you ask the questions.",
      'gloss': None,
      'is_agent': True},
    { "type": "Utterance",
      "text": "ok",
      "gloss": null,
      "is_agent": false},
    { "type": "Utterance",
      "text": "ok, I'm ready for questions",
      "gloss": null,
      "is_agent": true},
    { "type": "Utterance",
      "text": "is it a positive emotion?",
      "gloss": "unclassified-question",,
      "is_agent": false},
    { "type": "Utterance",
      "text": "yes",
      "gloss": "reply-to-question",
      "is_agent": true},
    #...
  ]
}

"""
    outdict = {}
    outdict["container"] = []
    for t in agent.episodicBuffer:
        if isinstance(t, AgentAskingTurn):
            outdict["container"].append({"type": "Question",
                                         "text": t.q.text,
                                         "gloss": t.q.gloss,
                                         "is_agent": t.q.is_agent})
            outdict["container"].append({"type": "Answer",
                                         "text": t.q.text,
                                         "gloss": t.q.gloss,
                                         "is_agent": t.q.is_agent})
        elif isinstance(t, IllocutionaryAct):
            outdict["container"].append({"type": "IllocutionaryAct",
                                         "params": t.args,
                                         "is_agent": True})

        else:
            outdict["container"].append({"type": "Utterance",
                                         "text": t.text,
                                         "gloss": t.gloss,
                                         "is_agent": t.is_agent})
            
    return outdict


if sys.argv[0].startswith("--"):
    if sys.argv[0].endswith("is-empty"):
        sys.argv.pop(0)
        for arg in sys.argv:
            agent = get_agent_from_session(arg)
            #print_turns(agent)
            obj = extract_json(agent)
            is_agent = list(map(lambda x: x.get("is_agent", True), obj['container']))
            empty = True
            for x in is_agent:
                if not x:
                    empty = False
            if all(list(is_agent)):
                print(arg)
            # if len(is_agent) > 20:
            #     import pdb
            #     pdb.set_trace()
    exit()

for arg in sys.argv:
    agent = get_agent_from_session(arg)
    #print_turns(agent)
    obj = extract_json(agent)
    #is_agent = map(lambda x: x.get("is_agent", True), obj['container'])
    #print(list(is_agent))
    #print(obj['container'])
    print(json.dumps(obj, indent="  "))
    print()
