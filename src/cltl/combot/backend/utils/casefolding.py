import re
import string


def casefold_text(text, format='triple'):
    if not text:
        return None

    if format == 'triple':
        if isinstance(text, str):
            for sign in string.punctuation:
                text = text.rstrip(sign)
                text = text.replace(sign, "-")

            text = text.lower().replace(" ", "-").strip('-')

        return re.sub('-+', '-', text)

    elif format == 'natural':
        return text.lower().replace("-", " ").strip() if isinstance(text, str) else text

    else:
        return text


def casefold_capsule(capsule, format='triple'):
    """
    Function for formatting a capsule into triple format or natural language format
    Parameters
    ----------
    capsule:
    format

    Returns
    -------

    """
    for k, v in list(capsule.items()):
        if isinstance(v, dict):
            capsule[k] = casefold_capsule(v, format=format)
        else:
            capsule[k] = casefold_text(v, format=format)

    return capsule
