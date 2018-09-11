# -*- coding: utf-8 -*-

import inspect

from django.db import models

limit_models = ["console", "order/orderservice", "site-packages/django", "order\\orderservice", "site-packages\\django"]


def lint_code(fn):
    def _wraper(*args, **kwargs):
        stacks = inspect.stack()
        is_limit = True
        for limit_model in limit_models:
            if limit_model in stacks[1][1]:
                is_limit = False
        if is_limit:
            raise Exception("please use order.orderservice module call order relation module, thx")
        result = fn(*args, **kwargs)
        return result

    return _wraper


class BaseLintManager(models.Manager):
    pass


def lint_manager(manager):
    attrs = dir(manager)
    for attr in attrs:
        if attr.startswith("_") or attr.startswith("__"):
            continue
        method = getattr(manager, attr)
        if inspect.isfunction(method):
            after_method = lint_code(method)
            setattr(manager, attr, after_method)
    return manager

BaseOrderManager = lint_manager(BaseLintManager)




