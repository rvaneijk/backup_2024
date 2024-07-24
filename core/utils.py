"""Utility functions for time-related operations."""

import time
from typing import Union, Optional

def timer(start_time: Optional[float] = None) -> Union[float, str]:
    """
    Measure elapsed time or return current time.

    This function can be used in two ways:
    1. Called without arguments, it returns the current time.
    2. Called with a start time, it returns the elapsed time as a formatted string.

    Args:
        start_time (float, optional): The start time in seconds since the epoch.
            If None, the current time will be returned. Defaults to None.

    Returns:
        Union[float, str]: If start_time is None, returns the current time as a float.
            Otherwise, returns the elapsed time as a formatted string (HH:MM:SS).

    Examples:
        >>> start = timer()
        >>> # ... do some work ...
        >>> elapsed = timer(start)
        >>> print(f"Time elapsed: {elapsed}")
    """
    if start_time is None:
        return time.time()
    else:
        elapsed_time = time.time() - start_time
        return time.strftime('%H:%M:%S', time.gmtime(elapsed_time))