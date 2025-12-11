"""Use Cases CLI Commands"""

from .list_usecases import setup_parser as setup_list_usecases_parser
from .get_usecase import setup_parser as setup_get_usecase_parser
from .list_datamodels import setup_parser as setup_list_datamodels_parser
from .get_datamodel import setup_parser as setup_get_datamodel_parser


def setup_parser(subparsers):
    """Setup all use case command parsers"""
    setup_list_usecases_parser(subparsers)
    setup_get_usecase_parser(subparsers)
    setup_list_datamodels_parser(subparsers)
    setup_get_datamodel_parser(subparsers)


__all__ = ['setup_parser']
