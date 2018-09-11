# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals


from django.core.management.base import BaseCommand, CommandError



class Command(BaseCommand):
    #
    # option_list = BaseCommand.option_list + (
    #     make_option('--user',  # 用户输入
    #                 action='store_true',
    #                 dest='user2',
    #                 default=False,  # 是否是默认的option
    #                 help="option's help message"),  # 此option的帮助信息，将在--help下显示
    # # )
    #
    # def add_arguments(self, parser):
    #     # Positional arguments
    #     parser.add_argument('poll_id', nargs='+', type=int)
    #
    #     # Named (optional) arguments
    #     parser.add_argument('--delete',
    #                         action='store_true',
    #                         dest='delete',
    #                         default=False,
    #                         help='Delete poll instead of closing it')

    def handle(self, *args, **options):
        print('handle')
