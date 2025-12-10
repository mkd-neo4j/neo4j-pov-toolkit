"""Use Cases CLI Commands"""

from .list_usecases import setup_parser as setup_list_usecases_parser
from .get_usecase import setup_parser as setup_get_usecase_parser


def setup_parser(subparsers):
    """Setup all use case command parsers"""
    setup_list_usecases_parser(subparsers)
    setup_get_usecase_parser(subparsers)


__all__ = ['setup_parser']
