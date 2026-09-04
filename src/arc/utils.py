from __future__ import annotations


__all__ = [
    "setup_logger",
]


# -- IMPORTS --

# -- Standard libraries --
import logging
import sys
import typing

from logging.handlers import TimedRotatingFileHandler

# -- 3rd party libraries --

# -- Internal libraries --


def setup_logger(name: str, **kwargs: typing.Any) -> None:
    """:py:class:`types.NoneType` : Sets up logging.

    Only the logger name is required. All other arguments are optional and
    keyword-based: see the :py:func:`logging.basicConfig` function definition
    for the full list of configurable logging properties.

    Parameters
    ----------
    name : str
        The logger name.

    **kwargs
        Optional keyword arguments for other logging properties such as level,
        message format, date format, stream, filename for the file handler etc.

    Examples
    --------
    >>> import logging; from arc.utils import setup_logger
    >>> logger = logging.getLogger("test")
    >>> logger.handlers
    []
    >>> logger = setup_logger("test")
    >>> assert logger.handlers
    >>> logger.handlers  # doctest: +SKIP
    [<StreamHandler (INFO)>, <TimedRotatingFileHandler /path/to/ARC/arc.log (INFO)>]
    >>> logger.info("A test logger")  # doctest: +SKIP
    2026-09-04 09:22:30 [INFO] test: A test logger
    """
    logger = logging.getLogger(name or "arc.log")
    level = kwargs.get("level", logging.INFO)
    logger.setLevel(level)

    if not logger.handlers:
        handlers = kwargs.get(
            "handlers",
            [
                logging.StreamHandler(kwargs.get("stream", sys.stdout)),
                TimedRotatingFileHandler(
                    "arc.log", when="d", interval=1, backupCount=5
                ),
            ],
        )
        formatter = logging.Formatter(
            kwargs.get("format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s"),
            kwargs.get("datefmt", "%Y-%m-%d %H:%M:%S"),
        )

        for handler in handlers:
            handler.setLevel(level)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    return logger
