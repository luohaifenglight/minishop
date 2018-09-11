#! coding: utf-8


import logging

from datetime import datetime
from django.db import transaction
from order.orderservice import OrderService, PushOrderMessage, PushTuanZhangMessage
from . import models


logger = logging.getLogger("django")

class PayService(object):

    @classmethod
    def save_order(cls, user_id, original, price, open_id, order_id, out_trade_id):
        save_dict = {
            "user_id": user_id,
            "out_trade_no": out_trade_id,
            "order_id": order_id,
            "price": str(price),
            "openid": open_id,
            "prepay_id": original.get("prepay_id"),
            "result_code": original.get("result_code", ""),
            "return_code": original.get("return_code", ""),
            "err_code": original.get("err_code", "")
        }
        models.WeChatPay.objects.update_or_create(out_trade_no=out_trade_id, defaults=save_dict)

    @classmethod
    def save_pay_order(cls, order):
        pays = models.WeChatPay.objects.get(out_trade_no=order.get("out_trade_no"))
        if not cls.check_pay(pays.order_id):
            logger.info(f"{pays.order_id}已经支付")
            return
        save_dict = {
            "transaction_id": order.get("transaction_id"),
            "out_trade_no": order.get("out_trade_no"),
            "time_end": order.get("time_end"),
            "total_fee": order.get("total_fee"),
            "trade_state": order.get("trade_state", ""),
            "ctime": datetime.strptime(order.get("time_end"), "%Y%m%d%H%M%S")
        }
        models.WeChatPay.objects.update_or_create(out_trade_no=order.get("out_trade_no"), defaults=save_dict)

        order_info = OrderService.pay_sccuess(pays.order_id, save_dict.get("ctime"))
        # send template message
        data = {
            "name": order_info.get("name"),
            "number": order_info.get("number"),
            "money": save_dict.get("total_fee"),
            "create_time": save_dict.get("ctime").strftime("%Y-%m-%d %H:%M:%S"),
            "way": "微信支付",
            "order_id": pays.order_id,
        }
        PushOrderMessage.send_message(pays.openid, pays.prepay_id, data)
        try:
            order_detail = OrderService.order_detail(pays.order_id)
            from passport.models import PassportUser
            seller = PassportUser.objects.get(id=order_detail.get("seller_id"))
            we_user = seller.wechatuser
            goods_titles = [d.get("title") for d in order_detail.get("goods")]
            data_tuanzhang = {
                "name": order_info.get("name"),
                "goods": "、".join(goods_titles),
                "price": order_detail.get("order_price"),
                "user_name": we_user.nickname,
                "money": save_dict.get("total_fee"),
                "create_time": save_dict.get("ctime").strftime("%Y-%m-%d %H:%M:%S"),
                "order_id": pays.order_id,
            }
            PushTuanZhangMessage.send_message(we_user.openid, pays.prepay_id, data_tuanzhang)
        except Exception as e:
            import traceback
            logger.exception(f'{e}')
        logger.info("openid%s, pay_id:%s", pays.openid, pays.prepay_id)

    @classmethod
    def check_pay(cls, order_id):
        return OrderService.check_pay(order_id)



    @classmethod
    @transaction.atomic
    def order_logic(cls, user_id, result_json, price, open_id, order_id, address, out_trade_no):
        PayService.save_order(user_id, result_json, price, open_id, order_id, out_trade_no)
        OrderService.pay(order_id, address, user_id)