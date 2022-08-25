#!/usr/bin/env python3

import pickle
import os
import sys

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
    print(sesh)
    #with open(os.path.join(session_dir, sesh), "rb") as f:
    with open(sesh, "rb") as f:    
        episodic_buffer, state_name, belief = pickle.load(f)
        agent = QAAgent(episodicBuffer=episodic_buffer,
                        lexicalAccess=LexicalAccess(),
                        semanticKnowledge=SemanticKnowledge())
    return agent
        
    
def print_turns(agent):
    for t in a.episodicBuffer:
        print(t)
        print()
    
if __name__ == "__main__":

    # check args
    if len(sys.argv) == 1:
        print("specify the session file")
        exit()

    for fname in sys.argv[1:]:
        print("fname:" + fname + ".")
        a = get_agent_from_session(fname)
        print_turns(a)
