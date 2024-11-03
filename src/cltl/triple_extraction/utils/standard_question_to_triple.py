

from cltl.triple_extraction.utils.helper_functions import extract_perspective

def standard_questions(utterance, human, agent):

    # https://github.com/leolani/cltl-knowledgerepresentation/blob/b96b7017a4420d8e59db2534321f8bd4c93fce76/src/cltl/brain/utils/base_cases.py#L1510

    triples = []
    if utterance.transcript.lower().startswith("what do ") or \
            utterance.transcript.lower().startswith("what does "):
        if utterance.transcript.lower().endswith(" have") or \
                utterance.transcript.lower().endswith(" own") or \
                utterance.transcript.lower().endswith(" have?") or \
                utterance.transcript.lower().endswith(" own?") :
            tokens = utterance.transcript.split()
            who = tokens[2]
            if who.lower() == "i":
                who = human
            elif who.lower() == "you":
                who = agent
            triple = {"subject": {"label": who.lower(), "type": [], "uri": None},
                      "predicate": {"label": "have", "type": [], "uri": None},
                      "object": {"label": "", "type": ["n2mu"], "uri": None},
                      "perspective": extract_perspective()
                      }
            triples.append(triple)
        elif utterance.transcript.lower().startswith("who "):
            tokens = utterance.transcript.split()
            if len(tokens ) >2:
                what = tokens[-1]
                predicate = tokens[1]
                if predicate.lower( )=="has":
                    predicate = "have"
                elif predicate.lower( )=="is":
                    predicate = "be"
                elif predicate.lower().endswith("s"):
                    predicate = predicate[:-1]
                if what.endswith("?"):
                    what = what[:-1]
                if what.lower() == "i":
                    what = human
                elif what.lower() == "you":
                    what = agent
                triple = {"subject": {"label": "", "type": [], "uri": None},
                          "predicate": {"label": predicate, "type": [], "uri": None},
                          "object": {"label": what.lower(), "type": ["n2mu"], "uri": None},
                          "perspective": extract_perspective()
                          }
                triples.append(triple)
    elif utterance.transcript.lower().startswith("who does ") and (utterance.transcript.lower().endswith(" know")
                                                                   or utterance.transcript.lower().endswith(" know?")):
        tokens = utterance.transcript.split()
        who = tokens[2]
        triple = {"subject": {"label": who.lower(), "type": [], "uri": None},
                  "predicate": {"label": "know", "type": [], "uri": None},
                  "object": {"label": "", "type": ["person"], "uri": None},
                  "perspective": extract_perspective()
                  }
        triples.append(triple)
    elif (utterance.transcript.lower().startswith("who is ") or
          utterance.transcript.lower().startswith("who are ") or
          utterance.transcript.lower().startswith("who do ") or
          utterance.transcript.lower().startswith("who does ")) and \
            (utterance.transcript.lower().endswith(" friend") or
             utterance.transcript.lower().endswith(" friends") or
             utterance.transcript.lower().endswith(" friend?") or
             utterance.transcript.lower().endswith(" friends?") or
             utterance.transcript.lower().endswith(" know?") or
             utterance.transcript.lower().startswith(" know?")):
        tokens = utterance.transcript.split()
        who = tokens[2]
        if who.endswith("'s"):
            who = who[:-2]
        if who.endswith("'"):
            who = who[:-1]
        if who.lower() == "my":
            who = human
        elif who.lower() == "your":
            who = agent
        if who.lower() == "i":
            who = human
        elif who.lower() == "you":
            who = agent
        triple = {"subject": {"label": who.lower(), "type": [], "uri": None},
                  "predicate": {"label": "know", "type": [], "uri": None},
                  "object": {"label": "", "type": ["person"], "uri": None},
                  "perspective": extract_perspective()
                  }
        print('TRIPLE IS', triple)
        triples.append(triple)
    elif utterance.transcript.lower().startswith("what are ") or \
            utterance.transcript.lower().startswith("what is ") or \
            utterance.transcript.lower().startswith("who are ") or \
            utterance.transcript.lower().startswith("who is "):
        tokens = utterance.transcript.split()
        who = tokens[-1]
        if who.endswith("?"):
            who = who[:-1]
        if who.lower() == "i":
            who = human
        elif who.lower() == "you":
            who = agent
        triple = {"subject": {"label": who.lower(), "type": [], "uri": None},
                  "predicate": {"label": "", "type": [], "uri": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"},
                  "object": {"label": "", "type": [], "uri": None},
                  "perspective":extract_perspective()
                  }
        triples.append(triple)
    elif utterance.transcript.lower().startswith("where are ") or \
            utterance.transcript.lower().startswith("where is "):
        tokens = utterance.transcript.split()
        who = tokens[-1]
        if who.endswith("?"):
            who = who[:-1]
        if who.lower() == "i":
            who = human
        elif who.lower() == "you":
            who = agent
        triple = {"subject": {"label": who.lower(), "type": [], "uri": None},
                  "predicate": {"label": "", "type": [], "uri": None},
                  "object": {"label": "", "type": ["n2mu:place"], "uri": None},
                  "perspective": extract_perspective()
                  }
        triples.append(triple)
    return triples

def ask_for_all(utterance, human, agent):
    triples = []
    if utterance.transcript.lower().startswith("tell me all about ") or \
            utterance.transcript.lower().startswith("tell me about ") or \
            utterance.transcript.lower().startswith("tell me all you know about ") or \
            utterance.transcript.lower().startswith("tell me what you know about ") or \
            utterance.transcript.lower().startswith("what you know about ") or \
            utterance.transcript.lower().startswith("what do you know about "):
        tokens = utterance.transcript.split()
        who = tokens[-1]
        if who.endswith("?"):
            who = who[:-1]
        if who.lower() == "me":
            who = human
        elif who.lower() == "you":
            who = agent
        elif who.lower().startswith("your"):
            who = agent
        triple = {"subject": {"label": who.lower(), "type": [], "uri": None},
                  "predicate": {"label": "", "type": ["n2mu:"], "uri": None},
                  "object": {"label": "", "type": [], "uri": None},
                  "perspective": extract_perspective()
                  }
        triples.append(triple)
        triple = {"subject": {"label": "", "type": [], "uri": None},
                  "predicate": {"label": "", "type": ["n2mu:"], "uri": None},
                  "object": {"label": who.lower(), "type": [], "uri": None},
                  "perspective": extract_perspective()
                  }
        triples.append(triple)
    return triples