#! coding: utf-8


import logging

from datetime import datetime
from django.db import transaction
from django.forms import model_to_dict
from django.core.cache import cache
from order.orderservice import OrderService, PushOrderMessage, PushTuanZhangMessage, OrderState
from . import models


logger = logging.getLogger("django")


class ReFundService(object):

    @classmethod
    def save_refund_order_scuess(cls, original, out_refund_no):
        save_dict = {
            "refund_fee": original.get("refund_fee"),
            "total_fee": original.get("total_fee"),
            "refund_id": original.get("refund_id", ""),
            "result_code": original.get("result_code", ""),
            "return_code": original.get("return_code", ""),
            "err_code": original.get("err_code", ""),
            "refund_state": OrderState.REFUNDING,
        }
        models.WeChatRefund.objects.update_or_create(out_refund_no=out_refund_no, defaults=save_dict)

    @classmethod
    def save_refund_order_fail(cls, order_id, reason):
        refund_order = cls._get_refund_order(order_id)
        save_dict = {
            "refund_state": OrderState.REFUND_FAILED,
            "fail_reason": reason
        }
        models.WeChatRefund.objects.update_or_create(out_refund_no=refund_order.out_refund_no, defaults=save_dict)
        OrderService.update_order_status(order_id, OrderState.REFUND_FAILED)

    @classmethod
    def create_refund_order(cls, order_id, pay_order, reason):
        save_dict = {
            "user_id": pay_order.user_id,
            "out_trade_no": pay_order.out_trade_no,
            "out_refund_no": pay_order.out_trade_no,
            "order_id": order_id,
            "transaction_id": pay_order.transaction_id,
            "price": str(pay_order.price),
            "refund_state": OrderState.APPLY_REFUNDING,
            "reason": reason,
        }
        from .wechartpay import local2utc
        models.WeChatRefund.objects.update_or_create(out_refund_no=pay_order.out_trade_no, defaults=save_dict)
        OrderService.update_order_status(order_id, OrderState.APPLY_REFUNDING, apply_refund_time=local2utc(datetime.now()))

    @classmethod
    def refund_sccuess(cls, order):
        save_dict = {
            "settlement_refund_fee": order.get("settlement_refund_fee"),
            "refund_status": order.get("refund_status"),
            "success_time": order.get("success_time"),
            "refund_recv_accout": order.get("refund_recv_accout"),
            "refund_account": order.get("refund_account", ""),
            "refund_request_source": order.get("refund_request_source", ""),
            "ctime": datetime.strptime(order.get("success_time"), "%Y-%m-%d %H:%M:%S")
        }
        orders = models.WeChatRefund.objects.get(out_refund_no=order.get("out_refund_no"))
        if orders.refund_state == OrderState.REFUNDED:
            logger.info(f"已经退款{ orders.order_id }")
            return
        if save_dict["refund_status"] == "SUCCESS":
            save_dict["refund_state"] = OrderState.REFUNDED
            OrderService.refund_statement(orders.order_id, orders.price)
            OrderService.update_order_status(orders.order_id, OrderState.REFUNDED)
        else:
            save_dict["refund_state"] = OrderState.REFUND_FAILED
            save_dict["fail_reason"] = "wechart failed"
            OrderService.update_order_status(orders.order_id, OrderState.REFUND_FAILED)
        OrderService.unfreeze(order.get("out_refund_no"))
        models.WeChatRefund.objects.update_or_create(out_refund_no=order.get("out_refund_no"), defaults=save_dict)
        # send template message

    @classmethod
    def _get_refund_order_status(cls, order_id):
        """
        get order refund state
        :param order_id: 
        :return: 
        """
        refunds = models.WeChatRefund.objects.filter(order_id=order_id).order_by("-create_time")[:1]
        if refunds:
            return refunds[0].refund_state
        return ""

    @classmethod
    def _get_refund_order(cls, order_id):
        """
        get order refund state
        :param order_id: 
        :return: 
        """
        refunds = models.WeChatRefund.objects.filter(order_id=order_id).order_by("-create_time")[:1]
        if refunds:
            return refunds[0]
        return ""

    @classmethod
    def _get_pay_order(cls, order_id):
        """
        get pay order
        :param order_id: 
        :return: 
        """
        orders = models.WeChatPay.objects.filter(order_id=order_id).exclude(time_end="").order_by("ctime")[:1]
        return orders[0] if orders else False

    @classmethod
    def get_format_refund_order(cls, order_id):
        order_formats = cls._get_refund_order(order_id)
        if order_formats:
            return model_to_dict(order_formats)
        return ""

    @classmethod
    @transaction.atomic
    def apply_refund(cls, user_id, order_id, reason=""):
        is_apply = cache.get(f"refund_{user_id}_{order_id}")
        if is_apply:
            return 1, "操作频繁", {}
        if not OrderService.jielong_status(order_id):
            return 1, "接龙已经结束", {}
        result = 0, "scuessfull", {}
        cache.set(f"refund_{user_id}_{order_id}", 1, 60)
        order = cls._get_pay_order(order_id)
        if not order:
            result = 1, "没有这个订单", {}
        refund_order_status = cls._get_refund_order_status(order_id)
        if refund_order_status:
            if refund_order_status not in [OrderState.APPLY_REFUNDING]:
                result = 2, "正在申请中", {}
        cls.create_refund_order(order_id, order, reason)
        cache.delete(f"refund_{user_id}_{order_id}")
        return result

    @classmethod
    @transaction.atomic
    def agree_refund(cls, user_id, order_id):

        balance = OrderService.get_balance(user_id)
        refund_order = cls._get_refund_order(order_id)
        if balance < refund_order.price:
            return 1, "您余额不足退款给买家", {}
        if not refund_order:
            return 1, "没有这个退款单", {}
        if refund_order.refund_state not in [OrderState.APPLY_REFUNDING]:
            return 1, "正在处理中", {}
        # need 统一错的情况
        # 。。。
        from .wechartpay import WechatRefund
        wp = WechatRefund()
        result_json = wp.apply_refund(refund_order.out_trade_no, refund_order.out_refund_no, refund_order.price)
        print(result_json)
        logger.info(result_json)
        if result_json.get("result_code", "") == "SUCCESS":
            cls.save_refund_order_scuess(result_json, refund_order.out_refund_no)
            # freeze money
            OrderService.freeze(user_id, refund_order.price, refund_order.out_refund_no)
            OrderService.update_order_status(order_id, OrderState.REFUNDING)
        else:
            return 1, result_json.get("err_code_des", ""), {}
        return 0, "scuessfull", {"order_id": order_id}

    @classmethod
    @transaction.atomic
    def disagree_refund(cls, user_id, order_id, reason=""):
        refund_order = cls._get_refund_order(order_id)
        if not refund_order:
            return 1, "没有这个退款单", {}
        if refund_order.refund_state not in [OrderState.APPLY_REFUNDING]:
            return 1, "正在处理中", {}
        cls.save_refund_order_fail(order_id, reason)
        return 0, "scuessfull", {"order_id": order_id}

    @classmethod
    def sync_refund_order(cls, order):
        req_info = order.get("req_info")
        from .wechartpay import WechatRefund
        result = WechatRefund.decrypt(req_info)
        order.update(result)
        cls.refund_sccuess(order)
