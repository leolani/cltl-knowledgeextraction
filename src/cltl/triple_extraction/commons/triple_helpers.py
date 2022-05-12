NOT_TO_MENTION_TYPES = ['instance']


def continuous_to_enum(enum_class, original_value):
    """
    Transform a continuous value to discrete
    :param enum_class: Class containing categories for perspective values
    :param original_value: Continuous value to be transformed
    :return:
    """
    try:
        new_value = enum_class(original_value)

    # The value given does not map exactly to a value in our enum, so we transform it
    except:
        mx = max([e.value for e in enum_class])
        mn = min([e.value for e in enum_class])
        range = mx - mn
        closest = round(range * original_value)

        new_value = enum_class(closest)

    return new_value


def fix_nlp_types(types):
    # type: (list) -> list
    """
    Takes list of types incoming from the NLP pipeline and filters out types that are not semantic but
    syntactic (e.g. adjective)
    Parameters
    ----------
    types: list

    Returns fixed_types: list
    -------

    """
    fixed_types = []
    for el in types:
        # this was just a char
        if len(el) == 1:
            fixed_types.append(types.split('.')[-1])
            break

        # Preferential types
        if "ability" in el:
            fixed_types.append('ability')

        elif "prediction" in el:
            fixed_types.append('prediction')

        elif "obligation" in el:
            fixed_types.append('obligation')

        elif "modal" in el:
            fixed_types.append('x')

        # Exclude this type
        elif "prep" == el or "adj" in el or "noun.Tops" in el or "article:definite" in el or "article:indefinite" in el:
            pass

        # need to corefer
        elif "deictic" in el or "pronoun" in el:
            pass

        # Take the more general part
        elif "article" in el or "prep" in el or "numeral" in el or "adv" in el:
            fixed_types.append(el.split('.')[0])

        # Take the more specific part
        elif '.' in el:
            fixed_types.append(el.split('.')[-1])

        # Take type as is
        else:
            fixed_types.append(el)

    # Hand fixed mappings
    if 'artifact' in fixed_types:
        fixed_types.append('object')

    if 'verb' in fixed_types or 'act' in fixed_types:
        fixed_types.append('action')

    return fixed_types


def filtered_types_names(types):
    types_names = ' or '.join([t for t in types if t.lower() not in NOT_TO_MENTION_TYPES])

    return types_names