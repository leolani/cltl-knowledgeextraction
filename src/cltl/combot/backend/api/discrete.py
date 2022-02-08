import enum


class Certainty(enum.Enum):
    UNDERSPECIFIED = 0
    POSSIBLE = 1
    PROBABLE = 2
    CERTAIN = 3


class Polarity(enum.Enum):
    UNDERSPECIFIED = 0
    NEGATIVE = -1
    POSITIVE = 1


class Sentiment(enum.Enum):
    UNDERSPECIFIED = 0
    NEGATIVE = -1
    POSITIVE = 1
    NEUTRAL = 2


class Emotion(enum.Enum):
    UNDERSPECIFIED = 0
    ANGER = 1
    DISGUST = 2
    FEAR = 3
    JOY = 4
    SADNESS = 5
    SURPRISE = 6
    NEUTRAL = 7


class Time(enum.Enum):
    UNDERSPECIFIED = 0
    PAST = 1
    PRESENT = 2
    FUTURE = 3


class UtteranceType(str, enum.Enum):
    STATEMENT = 0
    QUESTION = 1
    EXPERIENCE = 2
