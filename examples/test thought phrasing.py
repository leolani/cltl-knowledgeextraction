from cltl.language.api import Chat, UtteranceHypothesis
from cltl.language.generation.thoughts_phrasing import phrase_thoughts

brain = LongTermMemory(clear_all=False)

chat = Chat("Lenka")

# one or several statements are added to the brain

chat.add_utterance([UtteranceHypothesis(statement, 1.0)])
chat.last_utterance.analyze()
brain_response = brain.update(chat.last_utterance, reason_types=True)
reply = phrase_thoughts(brain_response, True, True)
print(reply)
