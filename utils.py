from typing import Optional


def int_parse(value: str) -> Optional[int]:
    """
    Parses an int
    :param value: string value to parse
    :return: the int, or None if failed
    """
    try:
        return int(value)
    except:
        return None