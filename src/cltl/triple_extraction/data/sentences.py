"""
Sets of Semantically Similar Phrases to add variety (using the random.choice function)
"""

import random

GREETING = [
    "Yo",
    "Hey!",
    "Hello!",
    "Hi!",
    "How's it going?",
    "How are you doing?",
    "What's up?",
    "What's new?",
    "What's going on?",
    "What's up?",
    "Good to see you!",
    "Nice to see you!",
]

TELL_KNOWN = [
    "Nice to see you again!",
    "It has been a long time!",
    "I'm glad we see each other again!",
    "You came back!",
    "At last!",
    "I was thinking about you!"
]

INTRODUCE = [
    "My name is Leo Lani!",
    "I'm Leo Lani.",
    "I am Leo Lani.",
    "I am a Pepper robot.",
    "I am a social robot.",
]

TELL_OBJECT = [
    "Guess what, I saw a {}",
    "Would you believe, I just saw a {}",
    "Did you know there's a {} here?",
    "I'm very happy, I saw a {}",
    "When you were not looking, I spotted a {}! Unbelievable!",
    "Have you seen the {}? I'm sure I did!"
]

OBJECT_NOT_SO_SURE = [
    "I'm not sure, but I see a {}!",
    "I don't think I'm correct, but it that a {}?",
    "Would that be a {}?",
    "I could be wrong, but I think I see a {}",
    "hmmmm, Just guessing, a {}?",
    "Haha, is that a {}?",
    "It's not clear to me, but would that be a {}?"
]

OBJECT_QUITE_SURE = [
    "I think that is a {}!",
    "That's a {}, if my eyes are not fooling me!",
    "I think I can see a {}!",
    "I can see a {}!",
]

OBJECT_VERY_SURE = [
    "That's a {}, I'm very very sure!",
    "I see it clearly, that is a {}!",
    "Yes, a {}!",
    "Awesome, that's a {}!"
]

ASK_NAME = [
    "What is your name?",
    "Who are you?",
    "I've told you my name, but what about yours?",
    "I would like to know your name!",
    "Can you tell me your name",
]

VERIFY_NAME = [
    "So you are called {}?",
    "Ah, your name is {}?",
    "Did I hear correctly your name is {}?",
    "I'm not sure, but is your name {}?",
    "Ok, is it {} then?"
]

DIDNT_HEAR_NAME = [
    "I didn't get your name.",
    "Sorry, I didn't get that.",
    "Oops, I didn't get your name.",
]

REPEAT_NAME = [
    "Could you repeat your name please?",
    "What is your name again?",
    "What did you say your name was?",
    "I don't understand single words that well, please try a sentence instead!",
    "I'm not good with all names, maybe try an English nickname if you will!",
    "Sorry, names are not my strong point. Could you repeat yours?",
]

JUST_MET = [
    "Nice to meet you, {}!",
    "It's a pleasure to meet you, {}!",
    "I'm happy to meet you, {}!",
    "Great we can be friends, {}!",
    "I hope we'll talk more often, {}!",
    "See you again soon, {}!"
]

MORE_FACE_SAMPLES = [
    "Let me have a good look at you, so I'll remember you!",
    "Can you show me your face, please? Then I'm sure I'll recognize you later",
    "Please let me have a look at you, then I'll know who you are!",
]

LOST_FACE = [
    "Oh, I lost you. Let's meet another time then!",
    "I got distracted, better next time!",
    "Ok, byebye, I'll meet you another time.",
    "Bye, There's time to meet later, I think!",
    "I'm confused, I hope you want to meet me later?",
]

DIFFERENT_FACE = [
    "Oh, I was meeting another person, but hi!",
    "Wow, you are different from last person. Hello to you!",
    "I can only handle one person at a time, else I get confused!"
]

THINKING = [
    "...Hm...",
    "...Well...",
    "...Right...",
    "...Okay...",
    "...You see...",
    "...Sure...",

    "...Let me think...",
    "...I'm thinking...",
    "...I heard you...",
    "...Let me tell you...",
    "...Give me a second...",
]

UNDERSTAND = [
    "I see!",
    "Right!",
    "Oke",
    "Sure!"
]

ADDRESSING = [
    "Well,",
    "Look,",
    "See,",
    "I'll tell you,"
]

ASK_FOR_QUESTIONS = [
    "Do you have a question for me?",
    "Ask me anything!",
]

USED_WWW = [
    "I looked it up on the internet",
    "I searched the web",
    "I made use of my internet sources",
    "I did a quick search"
]

HAPPY = [
    "Nice!",
    "Cool!",
    "Great!",
    "Wow!",
    "Superduper!",
    "Amazing!",
    "I like it!",
    "That makes my day!",
    "Incredible",
    "Mesmerizing"
]

ASK_ME = [
    "Ask me anything!",
    "Please ask me something",
]

SORRY = [
    "Sorry!",
    "I am sorry!",
    "Forgive me!",
    "My apologies!",
    "My humble apologies!",
    "How unfortunate!"
]

NO_ANSWER = [
    "I have no idea.",
    "I wouldn't know!",
    "I don't know"
]

THANK = [
    "Thank you!",
    "Thanks!",
    "I appreciate it",
    "That's great",
    "Cheers"
]

GOODBYE = [
    "Bye",
    "Bye Bye",
    "See you",
    "See you later",
    "Goodbye",
    "Have a nice day",
    "Nice talking to you"
]

AFFIRMATION = [
    "yes",
    "yeah",
    "correct",
    "right",
    "great",
    "true",
    "good",
    "well done",
    "correctamundo",
    "splendid",
    "indeed",
    "superduper",
    "wow",
    "amazing"
]

NEGATION = [
    "no",
    "nope",
    "incorrect",
    "wrong",
    "false",
    "bad",
    "stupid"
]

JOKE = [
    "Ok! What's the difference between a hippo? and a Zippo? Well, one is really heavy and the other is a little lighter.",
    "What's the difference between ignorance and apathy? I don't know and I don't care.",
    "Did you hear about the semi-colon that broke the law? He was given two consecutive sentences.",
    "Did you hear about the crook who stole a calendar? He got twelve months.",
    "Why is an island like the letter T? They're both in the middle of water!",
    "Did you hear the one about the little mountain? It's hilarious!",
    "I usually meet my friends at 12:59 because I like that one-to-one time.",
    "You can't lose a homing pigeon. If your homing pigeon doesn't come back, then what you've lost is a pigeon",
    "My friend got a personal trainer a year before his wedding. I thought: Oh my god! how long is the aisle going to be",
    "I needed a password eight characters long so I picked Snow White and the Seven Dwarves.",
    "I'm not a very muscular robot; the strongest thing about me is my password.",
    "Insomnia is awful. But on the plus side, only three more sleeps till Christmas.",
    "If you don't know what introspection is, you need to take a long, hard look at yourself",
    "Thing is, we all just want to belong. But some of us are short."
]

ELOQUENCE = [
    "I see",
    "Interesting",
    "Good to know",
    "I do not know, but I have a joke {}".format(random.choice(JOKE)),
    "As the prophecy foretold",
    "But at what cost?",
    "So let it be written, ... so let it be done",
    "So ... it   has come to this",
    "That's just what he/she/they would've said",
    "Is this why fate brought us together?",
    "And thus, I die",
    "... just like in my dream",
    "Be that as it may, still may it be as it may be",
    "There is no escape from destiny",
    "Wise words by wise men write wise deeds in wise pen",
    "In this economy?",
    "and then the wolves came",
    "Many of us feel that way",
    "I do frequently do not know things",
    "One more thing off the bucket list",
    "Now I have seen this too",
    "But, why?",
    "May I ask you why?",
    "Why?"
]

PARSED_KNOWLEDGE = ["I like learning things!",
                    "I'm always hungry for more information!",
                    "I will remember that!",
                    "Now that's an interesting fact!",
                    "I understand!"]

NEW_KNOWLEDGE = ["I did not know that!", "This is news to me.", "Interesting!", "Exciting news!",
                 "I just learned something,", "I am glad to have learned something new."]

EXISTING_KNOWLEDGE = ["This sounds familiar.", "That rings a bell.", "I have heard this before.", "I know."]

CONFLICTING_KNOWLEDGE = ["I am surprised.", "Really?", "This seems hard to believe.", "Odd!", "Are you sure?",
                         "I don't know what to make of this.", "Strange."]

CURIOSITY = ["I am curious.", "Let me ask you something.", "I would like to know.", "If you don't mind me asking."]

TRUST = ["I think I trust you.", "I trust you", "I believe you", "You have my trust."]

NO_TRUST = ["I am not sure I trust you.", "I do not trust you.", "I do not believe you."]

FUN_NLP_FACTS = [
    "Did you know that about 80% of data in the web is text? This is only an estimation, of course",
    "Did you know that one of the most active areas of Artificial Intelligence is Natural Language Processing? Language, in the end, is complicated. ",
    "Did you know that you can specialize in text mining to find patterns in what people communicate about? ",
    "As Adam Geitgey from Medium says ... Computers are great at working with structured data like spreadsheets and database tables. But humans usually communicate in words, not in tables. That's unfortunate for computers.",
    "Alexa, Siri and Cortana depend on language technologies like the ones you could learn",
    "Every second, on average, around 6,000 tweets are tweeted on Twitter. That is a lot of text! "
]
