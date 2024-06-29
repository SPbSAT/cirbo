"""Abstract base class for Circuit input data parser."""

import abc
import logging
import typing as tp

__all__ = ['AbstractParser']

logger = logging.getLogger(__name__)


class AbstractParser(metaclass=abc.ABCMeta):
    """
    Abstract base class for Circuit input data parser.

    Parser takes some "stream" of data as input, and processes it. Parser yields result
    during parsing. Input of Parser could be any iterable (types restricted only by
    specific Parser).

    """

    def convert(self, stream: tp.Iterable[str]) -> tp.Iterable:
        """
        Defines way elements are being collected from <stream>, and yields parsing
        result when possible.

        :param stream: Iterable, contains lines to parse.

        """
        logger.info("/" * 80)
        logger.info("Parsing started.")
        for line in stream:
            yield from self._process_line(line)
        yield from self._eof()
        logger.info("Parsing Ended.")
        logger.info("/" * 80)

    @abc.abstractmethod
    def _process_line(self, line: str) -> tp.Iterable:
        """
        Defines processing of one element (line) in input.

        :param line: line to process.

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _eof(self) -> tp.Iterable:
        """Defines additional output on end of file."""
        raise NotImplementedError()
