from typing import Any, List, Set, Tuple, Union


def ensure_iterable(value: Union[str, List[str], Tuple[str], Set[str], Any]) -> List[str]:
    """
    Ensure that a value is an iterable, even if it is a single value.

    :param value: The value to ensure is an iterable.
    :type value: Union[str, List[str], Tuple[str], Set[str], Any]

    :return: The value as a list.
    :rtype: List[str]
    """
    if isinstance(value, str):
        return value.split(",")
    elif not isinstance(value, (list, tuple, set)):
        return [value]
    return value
