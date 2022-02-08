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
