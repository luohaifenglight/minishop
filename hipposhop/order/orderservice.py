# -*- coding: utf-8 -*-
import decimal

import requests
import logging

from django.db import transaction
from django.core.cache import cache
from urllib.parse import urlencode

from utils.date_util import UtilDateTime
from .models import OrderUser, OrderDetail, Statement, FreezeAssert
from product.models import Product
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
from promotions.models import JieLong
from payment.wechartpay import local2utc, utc2local
from passport.models import PassportUser
from customer.models import Address, JieLongSpreadUserRelation
from django.db.models import Sum, Q, Count
from push.pushservice import PushBaseMessage


logger = logging.getLogger("django")

class OrderState(object):
    UNPAID = "unpaid"
    PAID = "paied"
    CANCEL = "cancel"
    SETTLED = "settled"
    APPLY_REFUNDING = "apply_refunding"
    REFUNDING = "refunding"
    REFUNDED = "refunded"
    REFUND_FAILED = "refund_failed"


class OrderService(object):

    OrderMap = {
        "apply_refunding": "申请退款中",
        "refunding": "退款中",
        "refunded": "退款成功",
        "refund_failed": "退款失败",

    }

    OrderMapColor = {
        "apply_refunding": "#566A97",
        "refunding": "#566A97",
        "refunded": "#888888",
        "refund_failed": "#E8413A",

    }

    def __init__(self, user_id):
        self.user_id = user_id

    def _check_sku_num(self, product):
        """
        校验商品库存量
        :param product: 
        :return: 
        """
        goods = Product.objects.get(id=product.get("id"))
        if goods.sku_num < int(product.get("product_num")):
            return False
        return True

    @classmethod
    def _sku_add_commond(cls, product):
        goods = Product.objects.select_for_update().get(id=product.get("id"))
        goods.sku_num = goods.sku_num - int(product.get("product_num"))
        # goods.volume = goods.volume + int(product.get("product_num"))
        goods.save()

    @classmethod
    def _sku_multi_commond(cls, order):
        goods = Product.objects.select_for_update().get(id=order.num_iid)
        goods.sku_num = goods.sku_num + int(order.item_num)
        # goods.volume = goods.volume - int(order.item_num)
        goods.save()

    @classmethod
    @transaction.atomic()
    def _add_volume(cls, order):
        goods = Product.objects.select_for_update().get(id=order.num_iid)
        goods.volume = goods.volume + int(order.item_num)
        goods.save()

    def _create_order_num(self):
        """
        生成订单编号
        100000000000000
        :return: 
        """

        order_key1 = "order_number1"
        default_num = 100000000000000
        order_num = cache.get(order_key1)
        if not order_num:
            trades = OrderUser.objects.all().order_by("-trade_parent_id")[:1]
            if not trades:
                order_num = default_num
            else:
                order_num = int(trades[0].trade_parent_id)
                order_num = (order_num / 100 + 1) * 100
        store_order = (order_num / 100 + 1) * 100
        cache.set(order_key1, store_order)
        return order_num

    def _create_child_order(self, parent_id, products):
        child_orders = []
        current_order_num = parent_id + 1
        total_price = Decimal("0.00")
        for product in products:
            self._sku_add_commond(product)
            good = Product.objects.get(id=product.get("id"))
            order_dict = {
                "num_iid": product.get("id"),
                "item_num": product.get("product_num"),
                "trade_id": current_order_num,
                "trade_parent_id": parent_id,
                "item_title": good.title,
                "price": good.zk_final_price,

            }
            total_price = total_price + good.zk_final_price * int(product.get("product_num"))
            child_orders.append(order_dict)
            current_order_num = current_order_num + 1
        return child_orders, total_price

    def _create_order(self, parent_id, jielong_id, spread_user_id, total_price):
        jielong = JieLong.objects.get(id=jielong_id)
        is_spread = self._is_spread(spread_user_id, jielong.passport_user.id)
        order_dict = {
            "trade_parent_id": parent_id,
            "batch_id": parent_id,
            "total_price": total_price,
            "buyer_id": self.user_id,
            # "seller_id": self.user_id,
            "seller_id": jielong.passport_user.id,
            "spread_user_id": spread_user_id or None,
            "is_reward": is_spread,
            "activity_id": jielong_id,
            "activity_name": jielong.title,
            "commission_rate": jielong.commission_rate if is_spread else 0,
        }
        return order_dict

    @classmethod
    def jielong_status(cls, order_id):
        order_detail = cls.order_detail(order_id)
        compare_time = local2utc(datetime.now())
        is_jielong = JieLong.objects.filter(id=order_detail.get("activity_id"), end_time__gt=compare_time, status=0).count()
        return is_jielong

    @transaction.atomic
    def create_order(self, jielong_id, spread_user_id, products):
        """
        下单
        :param products: 下单产品
        :return: 
        """
        compare_time = local2utc(datetime.now())
        is_jielong = JieLong.objects.filter(id=jielong_id, end_time__gt=compare_time, status=0).count()
        if not is_jielong:
            raise Exception("团购已经结束")
        for product in products:
            if not self._check_sku_num(product):
                raise Exception("库存不足")
        trade_parent_id = self._create_order_num()
        child_orders, total_price = self._create_child_order(trade_parent_id, products)
        parent_order = self._create_order(trade_parent_id, jielong_id, spread_user_id, total_price)

        # todo 订单入库
        OrderUser.objects.create(**parent_order)
        for child_order in child_orders:
            OrderDetail.objects.create(**child_order)
        return trade_parent_id

    def _value_count(self, order):
        """
        一些佣金计算，付款后计算
        :param order: 
        :return: 
        """
        pass

    def _is_spread(self, spread_user_id, user_id):
        if not spread_user_id or not user_id:
            return 0
        if JieLongSpreadUserRelation.objects.filter(passport_user_id=spread_user_id, invite_sponsor_id=user_id, status=1).count():
            return 1
        return 0



    @classmethod
    def pay_sccuess(cls, order_id, pay_time):
        ordre = OrderUser.objects.get(trade_parent_id=order_id)
        tax = cls.format_decimal_round(ordre.tax_rate * ordre.total_price)
        selle_price = ordre.total_price - tax
        commision = cls.format_decimal(selle_price * ordre.commission_rate / Decimal("100"))
        selle_price = cls.format_decimal(selle_price)
        update_dict = {
            "status": "paied",
            "pay_time": local2utc(pay_time),
            "commission": commision if ordre.is_reward else 0,
            "sell_price": selle_price,
            "pay_price": ordre.total_price

        }
        for k, v in update_dict.items():
            setattr(ordre, k, v)

        ordre.save()
        child_orders = OrderDetail.objects.filter(trade_parent_id=ordre.trade_parent_id)
        for child_order in child_orders:
            cls._add_volume(child_order)
        cls._update_statement(ordre)
        return {
            "name": ordre.activity_name,
            "number": 1
        }

    @classmethod
    def _update_statement(cls, order):
        activity = JieLong.objects.get(id=order.activity_id)
        statements = Statement.objects.filter(user_id=order.seller_id).order_by("-create_time")[:1]
        s_save_dict = {
            "user_id": order.seller_id,
            "type": 0,
            "account_type": 0, # 订单收入
            "desc": "团购下单 + %.2f元" % order.sell_price,
            "desc1": activity.title,
            "desc2": "已扣除手续费%.2f元" % (order.total_price * order.tax_rate),
            "money": order.sell_price,
            "balance": order.sell_price
        }
        if statements:
            statement = statements[0]
            balance = order.sell_price + statement.balance
            s_save_dict["balance"] = balance
        Statement.objects.create(**s_save_dict)
        if order.is_reward:
            cls._update_statement_spread(order)

    @classmethod
    def cash_statement(cls, user_id, money):
        statements = Statement.objects.filter(user_id=user_id).order_by("-create_time")[:1]
        s_save_dict = {
            "user_id": user_id,
            "type": 1,
            "account_type": 3,  # 提现支出
            "desc": "提现支出 - %.2f元" % money,
            "desc1": "微信提现",
            "desc2": "shouxufei",
            "money": money,
        }
        if statements:
            statement = statements[0]
            balance = statement.balance - Decimal(money)
            s_save_dict["balance"] = balance
        Statement.objects.create(**s_save_dict)
        return cls.get_balance(user_id)

    @classmethod
    def refund_statement(cls, order_id, money):
        order = cls.order_detail(order_id)
        user_id = order.get("seller_id")
        statements = Statement.objects.filter(user_id=user_id).order_by("-create_time")[:1]
        s_save_dict = {
            "user_id": user_id,
            "type": 1,
            "account_type": 4,  # 退款支出
            "desc": "退款支出 - %.2f元" % money,
            "desc1": "退款申请支出",
            "desc2": "shouxufei",
            "money": money,
        }
        if statements:
            statement = statements[0]
            balance = statement.balance - Decimal(money)
            s_save_dict["balance"] = balance
        Statement.objects.create(**s_save_dict)
        return cls.format_decimal(balance)

    @classmethod
    def freeze(cls, user_id, money, relation_id, reason="refund", type="refund"):
        save_dict = {
            "user_id": user_id,
            "price": money,
            "relation_id": relation_id,
            "type": type,
            "reason": reason,
        }
        FreezeAssert.objects.create(**save_dict)

    @classmethod
    def unfreeze(cls, relation_id, type="refund"):
        freeze_objects = FreezeAssert.objects.filter(relation_id=relation_id, type=type)
        for freeze_object in freeze_objects:
            freeze_object.status = "unfreeze"
            freeze_object.save()

    @classmethod
    def _get_freeze_money(cls, user_id):
        order_num_result = FreezeAssert.objects.filter(user_id=user_id, status="freeze").aggregate(
            order_num=Sum("price"))["order_num"]
        order_num_result = order_num_result if order_num_result else Decimal("0")
        return cls.format_decimal(order_num_result)

    @classmethod
    def _update_statement_spread(cls, order):
        if not order.commission:
            logger.info("000")
            return
        activity = JieLong.objects.get(id=order.activity_id)
        statements = Statement.objects.filter(user_id=order.spread_user_id).order_by("-create_time")[:1]
        s_save_dict = {
            "user_id": order.spread_user_id,
            "type": 0,
            "account_type": 1,  # 佣金收入
            "desc": "推广佣金 + %.2f元" % order.commission,
            "desc1": activity.title,
            "desc2": "shouxufei",
            "money": order.commission,
            "balance": order.commission
        }
        if statements:
            statement = statements[0]
            balance = order.commission + statement.balance
            s_save_dict["balance"] = balance
        Statement.objects.create(**s_save_dict)

        statements1 = Statement.objects.filter(user_id=order.seller_id).order_by("-create_time")[:1]
        s_save_dict1 = {
            "user_id": order.seller_id,
            "type": 1,
            "account_type": 1,  # 佣金收入
            "desc": "推广佣金 - %.2f元" % order.commission,
            "desc1": activity.title,
            "desc2": "shouxufei",
            "money": order.commission,
            "balance": order.commission
        }
        if statements1:
            statement = statements1[0]
            balance = statement.balance - order.commission
            s_save_dict1["balance"] = balance
        Statement.objects.create(**s_save_dict1)

    @classmethod
    def get_statement(cls, user_id, status):
        dicts = []
        statemetns = Statement.objects.filter(user_id=user_id, type=status, money__gt=0).order_by("-create_time")
        for statemetn in statemetns:
            return_dict = {
                "price_info": statemetn.desc,
                "order_info": statemetn.desc1,
                "charge": statemetn.desc2,
                "date_info": utc2local(statemetn.create_time).strftime("%Y-%m-%d %H:%M:%S")
            }
            dicts.append(return_dict)
        return dicts



    @classmethod
    @transaction.atomic
    def cancel_order(cls, order_id):
        ordre = OrderUser.objects.get(trade_parent_id=order_id)
        if ordre.status == "cancel":
            return False
        update_dict = {
            "status": "cancel",
            "commission": 0,
            "sell_price": 0,

        }
        for k, v in update_dict.items():
            setattr(ordre, k, v)
        child_orders = OrderDetail.objects.filter(trade_parent_id=ordre.trade_parent_id)
        for child_order in child_orders:
            cls._sku_multi_commond(child_order)
        ordre.save()

    @classmethod
    def pay(cls, order_id, address, user_id):
        from customer.models import Address
        address["user_id"] = user_id
        result = Address.objects.create(**address)
        order = OrderUser.objects.get(trade_parent_id=order_id)
        order.address_id = result.id
        order.save()

    @classmethod
    def format_order(cls, order, child_orders):
        goods = []
        for child_order in child_orders:
            goo = Product.objects.get(id=child_order.num_iid)
            good = {
                "id": child_order.num_iid,
                "title": child_order.item_title,
                "sku_desc": goo.sku_desc,
                "price": cls.format_decimal(child_order.price),
                "buy_num": child_order.item_num
            }
            goods.append(good)
        buyer = PassportUser.objects.get(id=order.buyer_id)
        jielong = JieLong.objects.get(id = order.activity_id)
        we_user = buyer.wechatuser
        return_json = {
            "user_id": order.buyer_id,
            "nickname": we_user.nickname,
            "avatar_url": we_user.avatar_url,
            "order_time": datetime.strptime(utc2local(order.create_time).strftime("%Y-%m-%d %H:%M:%S"),"%Y-%m-%d %H:%M:%S"),
            "order_price": cls.format_decimal(order.total_price),
            "trade_id": order.trade_parent_id,
            "activity_id": order.activity_id,
            "reward_price": cls.format_decimal(order.commission),
            "goods": goods,
            "seller_id": order.seller_id,
            "refund_info": cls.OrderMap.get(order.status, ""),
            "refund_state": cls.check_refund_state(order.status),
            "refund_info_color": cls.OrderMapColor.get(order.status, ""),
            "title":jielong.title
        }
        return return_json

    @classmethod
    def check_refund_state(cls, order_status):
        try:
            if order_status in cls.OrderMap:
                return order_status
            else:
                return ""
        except Exception as e:
            return ""

    @classmethod
    def update_order_status(cls, order_id, status, **kwargs):
        order = OrderUser.objects.get(trade_parent_id=order_id)
        order.status = status
        if kwargs:
            for k, v in kwargs.items():
                setattr(order, k, v)
        order.save()

    @classmethod
    def format_jielong_order(cls, order_data):
        from promotions import jielong_service
        order_list = []
        for o in order_data:
            goods_info = []
            for g in o["goods"]:
                g_info = "%s x %s" % (g["title"], g["buy_num"])
                goods_info.append(g_info)
            order_dict = {
                "id":o["trade_id"],
                "trade_id": o["trade_id"],
                "user_id":o["user_id"],
                "avatar_url":o["avatar_url"],
                "nickname":o["nickname"],
                "order_time":o["order_time"],
                "order_price":o["order_price"],
                "pay_info":"已付款：%s" % (o["order_price"]),
                "pay": "已付款：%s" % (o["order_price"]),
                "title":jielong_service.get_jielong_info_by_id(o["activity_id"]),
                "activity_id": o["activity_id"],
                "reward_price":o["reward_price"],
                "goods":goods_info,
                "refund_info": o["refund_info"],
                "refund_state": o["refund_state"],
                "refund_info_color": o["refund_info_color"]
            }
            order_list.append(order_dict)

        return order_list

    @classmethod
    def _parse_query_params(cls, **kwargs):
        user_id = kwargs.get("user_id")
        seller_id = kwargs.get("seller_id")
        jielong_id = kwargs.get("jielong_id")
        spread_user_id = kwargs.get("spread_user_id")
        spread_user_ids = kwargs.get("spread_user_ids")  # list
        other_query = kwargs.get("other_query")
        Q1 = ~Q(status__in=[OrderState.CANCEL, OrderState.UNPAID])
        if user_id is not None:
            Q1 = Q1 & Q(buyer_id=user_id)
        if jielong_id is not None:
            Q1 = Q1 & Q(activity_id=jielong_id)
        if seller_id is not None:
            Q1 = Q1 & Q(seller_id=seller_id)
        if spread_user_id is not None:
            Q1 = Q1 & Q(spread_user_id=spread_user_id)
        if spread_user_ids is not None and isinstance(spread_user_ids, list):
            Q1 = Q1 & Q(spread_user_id__in=spread_user_ids)
        if other_query is not None and isinstance(other_query, Q):
            Q1 = Q1 & other_query
        return Q1

    @classmethod
    def order_list(cls, page_size=20, page_no=1, *args, **kwargs):
        query = cls._parse_query_params(**kwargs)
        page_no = int(page_no) - 1
        page_no = page_no if page_no < 0 else page_no
        start = page_no * page_size
        end = (page_no + 1) * page_size
        count = OrderUser.objects.filter(query).count()
        orders = OrderUser.objects.filter(query).order_by("-create_time")[start:end]
        list_order = []
        print(query)
        for order in orders:
            child_order = OrderDetail.objects.filter(trade_parent_id=order.trade_parent_id)
            format_json = cls.format_order(order, child_order)
            list_order.append(format_json)
        return list_order, count

    @classmethod
    def _get_refund_Q(cls, refund_state=""):
        if refund_state:
            return Q(status=refund_state)
        return Q(status__in=[OrderState.APPLY_REFUNDING, OrderState.REFUND_FAILED, OrderState.REFUNDED,
                             OrderState.REFUNDING])

    @classmethod
    def refund_order_list(cls, page_size=20, page_no=1, refund_state="", *args, **kwargs):
        query = cls._parse_query_params(**kwargs)
        query = query & cls._get_refund_Q(refund_state)
        page_no = int(page_no) - 1
        page_no = page_no if page_no < 0 else page_no
        start = page_no * page_size
        end = (page_no + 1) * page_size
        count = OrderUser.objects.filter(query).count()
        orders = OrderUser.objects.filter(query).order_by("-apply_refund_time")[start:end]
        list_order = []
        print(query)
        for order in orders:
            child_order = OrderDetail.objects.filter(trade_parent_id=order.trade_parent_id)
            format_json = cls.format_order(order, child_order)
            list_order.append(format_json)
        return list_order, count

    @classmethod
    def order_queryset(cls, *args, **kwargs):
        """
        这个通用方法尽量不要用，除非必须要用到这个的时候才用。
        :param args: 
        :param kwargs: query params
        :return: query_set
        """
        query = cls._parse_query_params(**kwargs)
        query_set = OrderUser.objects.filter(query)
        return query_set

    @classmethod
    def total_order_price(cls, **kwargs):
        query = cls._parse_query_params(**kwargs)
        order_num_result = OrderUser.objects.filter(query).aggregate(
            order_num=Sum("total_price"))["order_num"]
        order_num_result = order_num_result if order_num_result else Decimal("0")
        return cls.format_decimal(order_num_result)

    @classmethod
    def total_commission_price(cls, **kwargs):
        query = cls._parse_query_params(**kwargs)
        order_num_result = OrderUser.objects.filter(query).aggregate(
            order_num=Sum("commission"))["order_num"]
        order_num_result = order_num_result if order_num_result else Decimal("0")
        return cls.format_decimal(order_num_result)

    @classmethod
    def count_data(cls, **kwargs):
        """
        统计数据
        :return: 
        """
        query = cls._parse_query_params(**kwargs)
        total_price = cls.total_order_price(**kwargs)
        order_num_result = OrderUser.objects.filter(query).aggregate(
            order_num=Sum("sell_price"))["order_num"]
        infact_price = order_num_result if order_num_result else Decimal("0")
        user_count = OrderUser.objects.filter(query).values_list("buyer_id", flat=True)
        user_count = list(set(list(user_count)))
        user_count = len(user_count)
        return_json = {
            "order_user_num": user_count,
            "order_num": OrderUser.objects.filter(query).count(),
            "order_total_price": cls.format_decimal(total_price),
            "order_commission_price": cls.format_decimal(cls.total_commission_price(**kwargs)),
            "order_wx_charge": cls.format_decimal(total_price - infact_price),
            "order_net_income": cls.format_decimal(infact_price)
        }
        return return_json

    @classmethod
    def statistic_sum(cls, filed_name, **kwargs):
        """
        :param filed_name: 求和字段
        :param kwargs: 
        :return: 
        """
        query = cls._parse_query_params(**kwargs)
        filed_sum_result = OrderUser.objects.filter(query).aggregate(
            filed_sum=Sum(filed_name))["filed_sum"]
        return cls.format_decimal(filed_sum_result)

    @classmethod
    def statistic_count(cls, **kwargs):
        query = cls._parse_query_params(**kwargs)
        filed_num_result = OrderUser.objects.filter(query).count()
        return filed_num_result

    @classmethod
    def order_detail(cls, order_id):
        order = OrderUser.objects.get(trade_parent_id=order_id)
        child_order = OrderDetail.objects.filter(trade_parent_id=order.trade_parent_id)
        format_json = cls.format_order(order, child_order)
        addresses = Address.objects.filter(id=order.address_id)
        address_info = {

        }
        if addresses:
            address = addresses[0]
            address_info = {
                "delivery": "快递发货",
                "receiver": address.name or format_json.get("nickname", ""),
                "tel": address.mobile,
                "address": "%s%s%s%s" % (address.province, address.country, address.city, address.address_detail)
            }
        format_json["comment"] = order.remark
        format_json["seller_comment"] = order.seller_remark
        format_json["address"] = address_info
        format_json["activity_id"] = order.activity_id
        return format_json

    @classmethod
    def check_pay(cls, order_id):
        order = OrderUser.objects.get(trade_parent_id=order_id)
        if order.status != "unpaid":
            return 0
        return 1

    @classmethod
    def get_balance(cls, user_id):
        statements = Statement.objects.filter(user_id=user_id).order_by("-create_time")[:1]
        if not statements:
           return Decimal("0.00")
        if statements:
            balancea = statements[0].balance
            balancea = balancea - cls._get_freeze_money(user_id)
            return cls.format_decimal(balancea)

    @classmethod
    def format_decimal(cls, decimal_num):
        if not decimal_num:
            return Decimal("0.00")
        if isinstance(decimal_num, Decimal):
            return decimal_num.quantize(Decimal('1.00'), ROUND_DOWN)
        if isinstance(decimal_num, str):
            return Decimal(decimal_num).quantize(Decimal('1.00'), ROUND_DOWN)

    @classmethod
    def format_decimal_round(cls, decimal_num):
        if not decimal_num:
            return Decimal("0.00")
        if isinstance(decimal_num, Decimal):
            return decimal_num.quantize(Decimal('0.00'))
        if isinstance(decimal_num, str):
            return Decimal(decimal_num).quantize(Decimal('0.00'))

    @classmethod
    def update_remark(cls, order_id, remark, type="buyer"):
        order = OrderUser.objects.get(trade_parent_id=order_id)
        if type == "buyer":
            order.remark = remark
        else:
            order.seller_remark = remark
        order.save()


class PushOrderMessage(PushBaseMessage):
    template_id = "O1PZqXfYTMqXMcgrFdSuY0WUxYbsnMhbRx_s_PYmUpE"

    @classmethod
    def format_data(cls, data):
        result = {
            "keyword1": {
                "value": data.get("name"),
            },
            "keyword2": {
                "value": data.get("number"),
            },
            "keyword3": {
                "value": "%s元" % OrderService.format_decimal(Decimal(data.get("money")) / 100),
            },
            "keyword4": {
                "value": data.get("create_time")
            },
            "keyword5": {
                "value": data.get("way"),
            },
            "keyword6": {
                "value": data.get("order_id")
            }
        }
        return result


class PushTuanZhangMessage(PushBaseMessage):
    template_id = "oTGicBkUnxftF7I9OA-1UZ1MZiqY0qnM9ifOYRMxycA"

    @classmethod
    def format_data(cls, data):
        result = {
            "keyword1": {
                "value": data.get("name"),
            },
            "keyword2": {
                "value": data.get("goods"),
            },
            "keyword3": {
                "value": f"{ OrderService.format_decimal(data.get('price')) }元" ,
            },
            "keyword4": {
                "value": data.get("user_name"),
            },
            "keyword5": {
                "value": f"{ OrderService.format_decimal(Decimal(data.get('money')) / 100) }元",
            },
            "keyword6": {
                "value": data.get("create_time"),
            },
            "keyword7": {
                "value": data.get("order_id")
            }
        }
        return result
