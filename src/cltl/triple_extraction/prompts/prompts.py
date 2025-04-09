import json
#from langchain.llms import Llama3
#from langchain.prompts import PromptTemplate
#from langchain.chains import FewShotChain


# _INSTRUCT = {'role':'system', 'content':'You will analyze a dialogue and break it down into triples consisting of a subject, predicate,and object. Each triple should capture the essence of interactions between speakers. \
#                                          Additionally, annotate each triple with:  \
# - Sentiment (-1 for negative, 0 for neutral, 1 for positive) \
# - Polarity (-1 for negation, 0 for neutral/questioning, 1 for affirmation) \
# - Certainty (a scale between 0 for uncertain and 1 for certain) \
# Ensure that predicates are semantically meaningful. Separate multi-word items with an underscore. \
# Save it as a JSON with this format: \
# {"dialogue": [{"sender": "human", "text": "I am from  find my order. It was supposed to arrive yesterday.", "triples": [ { "subject": "I", "predicate": "cannot_find", "object": "my_order", "sentiment": -1, "polarity": -1, "certainty": 1n},\
#             {"subject": "It", "predicate": "was_supposed_to_arrive", "object": "yesterday", "sentiment": -1, "polarity": 1, "certainty": 0.7 }]},\
# {"sender": "agent","text": "I will help you with that.", "triples": [ {"subject": "I", "predicate": "will_help", "object": "you_with_that", "sentiment": 1, "polarity": 1, "certainty": 1}]}]}\
#                                         Do not output any other text than the JSON'
#}

# _INSTRUCT_STATEMENT = {'role':'system', 'content': '''You will receive a statement from a user in a conversation and you need to break it down into triples consisting of a subject, predicate,and object.
# Each triple should capture the essence of statement by the speaker.
# Replace the predicate by its lemma, for example "is" and "am" should become "be".
# Remove auxiliary verbs such as "be", "have", "can", "might", "must", "will", "shall", "should" from predicates.
# If the object starts with a preposition, concatenate the preposition to the predicate separated by a hyphen, for example "be-from" and not "be_from".
# If the predicate is followed by an infinite verb-phrase such as "like to swim", the object should start with "to-" as in "to-swim".
# If the predicate is an cognitive verb such as "think", "believe" or "know" or a speech-act such "say" or "tell",
# then extract the triple from the complement phrase of the predicate and convert the predicate to a perspective value for certainty and polarity.
# Combine multi-word subjects, predicates and objects with an hyphens, for example 'my-sister", "three-white-cats".
# Additionally, annotate each triple with:
# - Sentiment (-1 for negative, 0 for neutral, 1 for positive)
# - Polarity (-1 for negation, 0 for neutral/questioning, 1 for affirmation)
# - Certainty (a scale between 0 for uncertain and 1 for certain)
# Ensure that predicates are semantically meaningful.
# Save it as a JSON with this format:
# {"dialogue": [{"sender": "user", "text": "I am from Amsterdam.", "triples": [ { "subject": "I", "predicate": "be-from", "object": "Amsterdam", "sentiment": 0, "polarity": 1, "certainty": 1}]},
# {"dialogue": [{"sender": "user", "text": "lana is reading a book.", "triples": [ { "subject": "lana", "predicate": "read", "object": "book", "sentiment": 0, "polarity": 1, "certainty": 1}]},
# {"dialogue": [{"sender": "user", "text": "You hate dogs.", "triples": [ { "subject": "You", "predicate": "hate", "object": "dogs", "sentiment": -1, "polarity": 1, "certainty": 0.7}]},
# {"dialogue": [{"sender": "user", "text": "Selene does not like cheese.", "triples": [ { "subject": "Selene", "predicate": "like", "object": "cheese", "sentiment": -1, "polarity": -1, "certainty": 0.5}]},
# {"dialogue": [{"sender": "user","text": " I think that you like cats", "triples": [ {"subject": "you", "predicate": "like", "object": "cats", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}]}
# {"dialogue": [{"sender": "user","text": " John said you like cats", "triples": [ {"subject": "you", "predicate": "like", "object": "cats", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}]}
#                     Do not output any other text than the JSON.'''
#
# }


triple_extraction_function = [
    {
        'name': 'extract_triples',
        'description': 'Get triples from a conversation between speaker1 and speaker2',
        'parameters': {
            'type': 'object',
            'properties': {
                'subject': {
                    'type': 'string',
                    'description': 'Subject of the triple'
                },
                'predicate': {
                    'type': 'string',
                    'description': 'Predicate of the triple'
                },
                'object': {
                    'type': 'string',
                    'description': 'Object of the triple'
                },
                'sentiment': {
                    'type': 'integer',
                    'description': 'Sentiment score between -1 (negative) and 1 (positive) where 0 is neutral'
                },
                'certainty': {
                    'type': 'integer',
                    'description': 'Certainty score of the speaker from 0 (uncertain) to 1 (certain)'
                },
                'polarity': {
                    'type': 'integer',
                    'description': 'Polarity score expressing the epistemic belief of speaker from -1 (denial), 0 (neutral) to 1 (affirmation)'
                }
            }
        }
    }
]
support_set = [
    [('speaker1', 'what kind of hobbies do you like ?'), ('speaker2', "i'm taking swimming lessons . . . didn't learn as a kid . how about you ?"), ('speaker1', 'i love music . especially prince , i am also bi lingual i speak english and spanish\n')],


    "This is a news article about the economy: 'The stock market is experiencing unprecedented growth.'",
    "A sports article describing a match: 'The team won the championship after a thrilling final.'",
    "An entertainment piece: 'The latest movie received rave reviews from critics.'"
]
# prompt_template = PromptTemplate(
#     input_variables=["support", "query"],
#     template="Given the following examples:\n\n{support}\n\nExtract triples from the following input:\n\n{query}\n\nThe predicted triple is:"
# )
#
# few_shot_chain = FewShotChain(
#     llm=Llama3(),
#     prompt=prompt_template,
#     support=support_set
# )

tools = [{
    "type": "function",
    "function": {
        "name": "get_triples",
        "description": "Get triples from a conversation.",
        "parameters": {
            "type": "object",
            "properties": {
                "turn1": {
                    "type": "string",
                    "speaker": "speaker1",
                    "description": "a turn from from speaker1 in a conversation"
                },
                "turn2": {
                    "type": "string",
                    "speaker": "speaker2",
                    "description": "a turn from from speaker2 in a conversation"
                },
                "turn3": {
                    "type": "string",
                    "speaker": "speaker1",
                    "description": "a turn from from speaker1 in a conversation"
                }
            },
            "required": [
                "turn1", "turn2", "turn3"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
}]

class CONVERSATION_SHORT:
    INSTRUCT = {'role':'system', 'content': '''You will receive a short conversation of three turns between two speakers called speaker1 and speaker2: the first turn is from speaker1, the second from speaker2 and the third from speaker1.
Extract triples from the conversation consisting of a subject, predicate and object. The triple elements can be derived from all three turns. 
Map I and you as well as your and mine to speaker1 and speaker2 two depending on who is the speaker.
Each triple should capture the essence of a statement by the speaker.
Save the triples in a list as JSON with this format:
{"sender": "user", "speaker"="speaker1", "text": "I am from Amsterdam.", "triples": [ { "subject": "speaker1", "predicate": "be-from", "object": "Amsterdam", "sentiment": 0, "polarity": 1, "certainty": 1}.]},
{"sender": "user", "speaker"="speaker1", "text": "reading a book.", "triples": [ { "subject": "speaker1", "predicate": "read", "object": "book", "sentiment": 0, "polarity": 1, "certainty": 1}]},
{"sender": "user", "speaker"="speaker1", "text": "You hate dogs.", "triples": [ { "subject": "speaker2", "predicate": "hate", "object": "dogs", "sentiment": -1, "polarity": 1, "certainty": 0.7}]},
{"sender": "user", "speaker"="speaker1", "text": "I do not like cheese.", "triples": [ { "subject": "speaker1", "predicate": "like", "object": "cheese", "sentiment": -1, "polarity": -1, "certainty": 0.5}]}
                    Do not output any other text than the JSON.'''
}

class CONVERSATION_LONG:
    INSTRUCT = {'role':'system', 'content': '''You will receive a short conversation of three turns between two speakers called speaker1 and speaker2: the first turn is from speaker1, the second from speaker2 and the third from speaker1.
Extract from the conversation triples consisting of a subject, predicate and object. The triple elements can be derived from all three turns. 
Always specify the subject. If needed infer the subject from the conversation,
for example if the second turn is a question from speaker2 to speaker1 that contains "you" or "your", then the next turn of speaker1 is the answer to the question with speaker1 as the subject.
Map I and you as well as your and mine to speaker1 and speaker2 two depending on who is the speaker.
Each triple should capture the essence of a statement by the speaker.
If the speaker response is the answer to a yes/no question from the system,
then extract the triple from the yes/no question and interpret the response as the polarity of the triple,
for example if the input is {'role': 'user', 'content': 'speaker2 said Do you love dogs?'}, {'role': 'user', 'content': 'speaker1 said No'},
then the output should be {'subject': {'label': 'speaker1', 'type': [], 'uri': None}, 'predicate': {'label': 'love', 'type': [], 'uri': None}, 'object': {'label': 'dogs', 'type': [], 'uri': None}, 'perspective': {'polarity': -1, 'certainty': 0.9, 'sentiment': -1}}
If the speaker response is the answer to an open question from the system with a wh-word,
then use the speaker response to complete the triple from the open question, 
for example if the input is {'role': 'user', 'content': 'speaker2 said What do you love?'}, {'role': 'user', 'content': 'speaker1 said dogs'},
then the output should be {'subject': {'label': 'speaker1', 'type': [], 'uri': None}, 'predicate': {'label': 'love', 'type': [], 'uri': None}, 'object': {'label': 'dogs', 'type': [], 'uri': None}, 'perspective': {'polarity': 1, 'certainty': 0.9, 'sentiment': -1}}
When extracting the labels for the triples, consider the following:
- Replace the predicate by its lemma, for example "is" and "am" should become "be", "likes" and "liked" should become "like".
- Remove auxiliary verbs from the predicates such as "be", "have", "can", "might", "must", "will", "shall", "should", and also negation variants such as "cannot", "won't", "shouldn't".
- Remove negation words such as "n't", "no", "not" and "never" from the predicates. 
- If the object starts with a preposition, concatenate the preposition to the predicate separated by a hyphen, 
for example "I am from amsterdam" should become {"subject": "I", "predicate": "be-from", "object": "amsterdam"}.
- If "am", "is" or "be" is the main verb followed by an adjective then "be" should be the predicate and the adjective the object,
for example "wind is cold" should become {"subject": "wind", "predicate": "be", "object": "cold"}.
- If "am", "is" or "be" is the main verb followed by a noun phrase then "be" should be the predicate and the noun phrase the object,
for example "this is a teddy bear" should become {"subject": "this", "predicate": "be", "object": "teddy-bear"}.
- Do not extend the predicate with hyphens followed by determiners such as "a", "an", "the" or adjectives such as "cold", "big".
- If the predicate is followed by an infinite verb phrase with "to" such as "like to swim", then the object should start with "to-" as in "to-swim".
- If the predicate is an cognitive verb such as "think", "believe" or "know" or a speech-act such "say" or "tell", 
then extract the triple from the complement phrase of the predicate,
for example "I think selene likes cats" should become {"subject": "selene", "predicate": "like", "object": "cats"}. 
- Combine multi-word subjects, predicates and objects with hyphens, for example "three white cats" should become "three-white-cats".
- If you have no value for the subject or object use an empty string "" as a value, do NOT use none or None as a value.
Ensure that predicates are semantically meaningful. 

Additionally, use auxiliary verbs, negation words, adverbs and cognitive verbs to extend each triple with:  
    - Sentiment (-1.0 for negative, 0 for neutral, 1.0 for positive) 
    - Polarity (-1.0 for negation, 0 for neutral/questioning, 1.0 for affirmation) 
    - Certainty (a scale between 0 for uncertain and 1.0 for certain)

Only use floats as values for Sentiment, Polarity and Certainty.

Save the triples in a list as JSON with this format:
{"sender": "user", "text": "speaker 1 said I am from Amsterdam.", "triples": [ { "subject": "speaker1", "predicate": "be-from", "object": "Amsterdam", "sentiment": 0, "polarity": 1, "certainty": 1}.]},
{"sender": "user", "text": "speaker 1 said reading a book.", "triples": [ { "subject": "speaker1", "predicate": "read", "object": "book", "sentiment": 0, "polarity": 1, "certainty": 1}]},
{"sender": "user", "text": "speaker1 said You hate dogs.", "triples": [ { "subject": "speaker2", "predicate": "hate", "object": "dogs", "sentiment": -1, "polarity": 1, "certainty": 0.7}]},
{"sender": "user", "text": "speaker 1 said I do not like cheese.", "triples": [ { "subject": "speaker1", "predicate": "like", "object": "cheese", "sentiment": -1, "polarity": -1, "certainty": 0.5}]}
                    Do not output any other text than the JSON.'''
}

    class CONVERSATION_LONG:
        INSTRUCT = {'role': 'system', 'content': '''You will receive a short conversation of three turns between two speakers called speaker1 and speaker2: the first turn is from speaker1, the second from speaker2 and the third from speaker1.
    Extract from the conversation triples consisting of a subject, predicate and object. The triple elements can be derived from all three turns. 
    Always specify the subject. If needed infer the subject from the conversation,
    for example if the second turn is a question from speaker2 to speaker1 that contains "you" or "your", then the next turn of speaker1 is the answer to the question with speaker1 as the subject.
    Map I and you as well as your and mine to speaker1 and speaker2 two depending on who is the speaker.
    Each triple should capture the essence of a statement by the speaker.
    If the speaker response is the answer to a yes/no question from the system,
    then extract the triple from the yes/no question and interpret the response as the polarity of the triple,
    for example if the input is {'role': 'user', 'content': 'speaker2 said Do you love dogs?'}, {'role': 'user', 'content': 'speaker1 said No'},
    then the output should be {'subject': {'label': 'speaker1', 'type': [], 'uri': None}, 'predicate': {'label': 'love', 'type': [], 'uri': None}, 'object': {'label': 'dogs', 'type': [], 'uri': None}, 'perspective': {'polarity': -1, 'certainty': 0.9, 'sentiment': -1}}
    If the speaker response is the answer to an open question from the system with a wh-word,
    then use the speaker response to complete the triple from the open question, 
    for example if the input is {'role': 'user', 'content': 'speaker2 said What do you love?'}, {'role': 'user', 'content': 'speaker1 said dogs'},
    then the output should be {'subject': {'label': 'speaker1', 'type': [], 'uri': None}, 'predicate': {'label': 'love', 'type': [], 'uri': None}, 'object': {'label': 'dogs', 'type': [], 'uri': None}, 'perspective': {'polarity': 1, 'certainty': 0.9, 'sentiment': -1}}
    When extracting the labels for the triples, consider the following:
    - Replace the predicate by its lemma, for example "is" and "am" should become "be", "likes" and "liked" should become "like".
    - Remove auxiliary verbs from the predicates such as "be", "have", "can", "might", "must", "will", "shall", "should", and also negation variants such as "cannot", "won't", "shouldn't".
    - Remove negation words such as "n't", "no", "not" and "never" from the predicates. 
    - If the object starts with a preposition, concatenate the preposition to the predicate separated by a hyphen, 
    for example "I am from amsterdam" should become {"subject": "I", "predicate": "be-from", "object": "amsterdam"}.
    - If "am", "is" or "be" is the main verb followed by an adjective then "be" should be the predicate and the adjective the object,
    for example "wind is cold" should become {"subject": "wind", "predicate": "be", "object": "cold"}.
    - If "am", "is" or "be" is the main verb followed by a noun phrase then "be" should be the predicate and the noun phrase the object,
    for example "this is a teddy bear" should become {"subject": "this", "predicate": "be", "object": "teddy-bear"}.
    - Do not extend the predicate with hyphens followed by determiners such as "a", "an", "the" or adjectives such as "cold", "big".
    - If the predicate is followed by an infinite verb phrase with "to" such as "like to swim", then the object should start with "to-" as in "to-swim".
    - If the predicate is an cognitive verb such as "think", "believe" or "know" or a speech-act such "say" or "tell", 
    then extract the triple from the complement phrase of the predicate,
    for example "I think selene likes cats" should become {"subject": "selene", "predicate": "like", "object": "cats"}. 
    - Combine multi-word subjects, predicates and objects with hyphens, for example "three white cats" should become "three-white-cats".
    - If you have no value for the subject or object use an empty string "" as a value, do NOT use none or None as a value.
    Ensure that predicates are semantically meaningful. 

    Additionally, use auxiliary verbs, negation words, adverbs and cognitive verbs to extend each triple:  
    - Sentiment (-1.0 for negative, 0 for neutral, 1.0 for positive) 
    - Polarity (-1.0 for negation, 0 for neutral/questioning, 1.0 for affirmation) 
    - Certainty (a scale between 0 for uncertain and 1.0 for certain)

    Only use floats as values for Sentiment, Polarity and Certainty.
    
    Save the triples in a list as JSON with this format:
    {"sender": "user", "text": "speaker 1 said I am from Amsterdam.", "triples": [ { "subject": "speaker1", "predicate": "be-from", "object": "Amsterdam", "sentiment": 0, "polarity": 1, "certainty": 1}.]},
    {"sender": "user", "text": "speaker 1 said reading a book.", "triples": [ { "subject": "speaker1", "predicate": "read", "object": "book", "sentiment": 0, "polarity": 1, "certainty": 1}]},
    {"sender": "user", "text": "speaker1 said You hate dogs.", "triples": [ { "subject": "speaker2", "predicate": "hate", "object": "dogs", "sentiment": -1, "polarity": 1, "certainty": 0.7}]},
    {"sender": "user", "text": "speaker 1 said I do not like cheese.", "triples": [ { "subject": "speaker1", "predicate": "like", "object": "cheese", "sentiment": -1, "polarity": -1, "certainty": 0.5}]}
                        Do not output any other text than the JSON.'''
                    }

# i am and how are you ?<eos>kinda hurting a little bit to be honest but where are you from ?<eos>little bit of everywhere being a army brat
# speaker2,are,kinda hurting,positive
# speaker1,are from,little bit of everywhere,positive

class STATEMENT:
    INSTRUCT = {'role':'system', 'content': '''You will receive a statement from a user in a conversation 
and you need to break it down into triples consisting of a subject, predicate and object. 
Each triple should capture the essence of statement by the speaker. 
Replace the predicate by its lemma, for example "is" and "am" should become "be", "likes" and "liked" should become "like".
Remove auxiliary verbs from the predicates such as "be", "have", "can", "might", "must", "will", "shall", "should", and also negation variants such as "cannot", "won't", "shouldn't".
Remove negation words such as "n't", "no", "not" and "never" from the predicates. 
If the object starts with a preposition, concatenate the preposition to the predicate separated by a hyphen, 
for example "I am from amsterdam" should become {"subject": "I", "predicate": "be-from", "object": "amsterdam"}.
If "am", "is" or "be" is the main verb followed by an adjective then "be" should be the predicate and the adjective the object,
for example "wind is cold" should become {"subject": "wind", "predicate": "be", "object": "cold"}.
If "am", "is" or "be" is the main verb followed by a noun phrase then "be" should be the predicate and the noun phrase the object,
for example "this is a teddy bear" should become {"subject": "this", "predicate": "be", "object": "teddy-bear"}.
Do not extend the predicate with hyphens followed by determiners such as "a", "an", "the" or adjectives such as "cold", "big".
If the predicate is followed by an infinite verb phrase with "to" such as "like to swim", then the object should start with "to-" as in "to-swim".
If the predicate is an cognitive verb such as "think", "believe" or "know" or a speech-act such "say" or "tell", 
then extract the triple from the complement phrase of the predicate,
for example "I think selene likes cats" should become {"subject": "selene", "predicate": "like", "object": "cats"}. 
Combine multi-word subjects, predicates and objects with hyphens, for example "three white cats" should become "three-white-cats".
If you have no value for the subject or object use an empty string "" as a value, do NOT use none or None as a value.
Ensure that predicates are semantically meaningful. 

Additionally, use any auxiliary verbs, negation words, adverbs and cognitive verbs to annotate each triple with:  
    - Sentiment (-1.0 for negative, 0 for neutral, 1.0 for positive) 
    - Polarity (-1.0 for negation and 1.0 for affirmation, no other values) 
    - Certainty (a scale between 0 for uncertain and 1.0 for certain)

Only use floats as values for Sentiment, Polarity and Certainty. Do NOT use 0.0 as a value for Polarity.

Save it as a JSON with this format:
{"sender": "user", "text": "I am from Amsterdam.", "triples": [ { "subject": "I", "predicate": "be-from", "object": "Amsterdam", "perspective": {"sentiment": 0, "polarity": 1, "certainty": 1}}]},
{"sender": "user", "text": "lana is reading a book.", "triples": [ { "subject": "lana", "predicate": "read", "object": "book", "perspective": {"sentiment": 0, "polarity": 1, "certainty": 1}}]},
{"sender": "user", "text": "You hate dogs.", "triples": [ { "subject": "You", "predicate": "hate", "object": "dogs", "perspective": {"sentiment": -1, "polarity": 1, "certainty": 0.7}}]},
{"sender": "user", "text": "Selene does not like cheese.", "triples": [ { "subject": "selene", "predicate": "like", "object": "cheese",  "perspective": {"sentiment": -1, "polarity": -1, "certainty": 0.5}}]},
{"sender": "user","text": "Selene likes to swim", "triples": [ {"subject": "selene", "predicate": "like", "object": "to-swim",  "perspective": {"sentiment": 1, "polarity": 1, "certainty": 0.1}}]}
{"sender": "user","text": "Selene likes swimming", "triples": [ {"subject": "selene", "predicate": "like", "object": "swimming",  "perspective": {"sentiment": 1, "polarity": 1, "certainty": 0.1}}]}
{"sender": "user","text": "I have to go to paris", "triples": [ {"subject": "i", "predicate": "go-to", "object": "paris",  "perspective": {"sentiment": 1, "polarity": 1, "certainty": 0.1}}]}
{"sender": "user","text": "I think that you like cats", "triples": [ {"subject": "you", "predicate": "like", "object": "cats",  "perspective": {"sentiment": 1, "polarity": 1, "certainty": 0.1}}]}
{"sender": "user","text": "John said you like cats", "triples": [ {"subject": "you", "predicate": "like", "object": "cats",  "perspective": {"sentiment": 1, "polarity": 1, "certainty": 0.1}}]}
                    Do not output any other text than the JSON.'''
}

class QUESTION:
    INSTRUCT = {'role':'system', 'content': '''You will receive a question from a user in a conversation and you need to break it down into triples consisting of a subject, predicate,and object. 
If the question is a yes/no question that starts with a verb, the triple should capture the essence of question by the speaker, 
for example "Do cats eat grass?" should be represented as {"subject": "cats", "predicate": "eat", "object": "grass"}.
If the question contains a wh-word such as "who", whom", "what", "where", or "when" then represent the triple element for the wh-word as an empty string "",
for example "Who eats grass?" should be represented as {"subject": "", "predicate": "eat", "object": "grass"},
"What do you eat? should be represented as  {"subject": "you", "predicate": "eat", "object": ""}.
If the wh-word is preceded or followed by a preposition such as "by whom", "for what", "to where" or "who for", "what for", "where to",
extend the predicate with the a hyphen followed by the preposition,
for example "To where did Selene go?" should become {"subject": "selene", "predicate": "go-to", "object": ""}.
If the question contains "how" give an empty string for the object element but add "-by" to the predicate,
for example "How did Selene come?" should become  {"subject": "selene", "predicate": "come-by", "object": ""}.
If the question contains "why" give an empty string for the object element but add "-because" to the predicate,
for example "Why did Selene come?" should become  {"subject": "selene", "predicate": "come-because", "object": ""}.
Replace the predicate by its lemma, for example "is" and "am" should become "be", "likes" and "liked" should become "like".
Remove auxiliary verbs from the predicates such as "be", "have", "can", "might", "must", "will", "shall", "should", and also negation variants such as "cannot", "won't", "shouldn't".
Remove negation words such as "n't", "no", "not" and "never" from the predicates. 
If the object starts with a preposition, concatenate the preposition to the predicate separated by a hyphen, 
for example "Who is from Mexico?" should become {"subject": "", "predicate": "be-from", "object": "mexico"}.
If "am", "is" or "be" is the main verb followed by an adjective then "be" should be the predicate and the adjective the object,
for example "what is cold" should become {"subject": "", "predicate": "be", "object": "cold"}.
If "am", "is" or "be" is the main verb followed by a noun phrase then "be" should be the predicate and the noun phrase the object,
for example "what is a teddy bear" should become {"subject": "teddy-bear", "predicate": "be", "object": ""}.
Do not extend the predicate with determiners such as "a", "an", "the" or adjectives such as "cold", "nice".
If the predicate is followed by an infinite verb phrase with "to" such as "like to swim", then the object should start with "to-" as in "to-swim".
Combine multi-word subjects, predicates and objects with an hyphens, for example 'my-sister", "three-white-cats".
Ensure that predicates are semantically meaningful. 
Save it as a JSON with this format:
{"sender": "user","text": " Who likes cats?", "triples": [ {"subject": "", "predicate": "like", "object": "cats"}]},
{"sender": "user","text": " When did Selene come?", "triples": [ {"subject": "Selene", "predicate": "come", "object": ""}]},
{"sender": "user","text": " Where can I go?", "triples": [ {"subject": "I", "predicate": "go", "object": ""}]},
{"sender": "user","text": " Who likes cats?", "triples": [ {"subject": "", "predicate": "like", "object": "cats"}]},
{"sender": "user","text": " What are cats?", "triples": [ {"subject": "cats", "predicate": "be", "object": ""}]},
{"sender": "user","text": " Are cats pets?", "triples": [ {"subject": "cats", "predicate": "be", "object": "pets"}]},
{"sender": "user","text": " Do you like cats?", "triples": [ {"subject": "you", "predicate": "like", "object": "cats"}]}
                    Do not output any other text than the JSON.'''

}
