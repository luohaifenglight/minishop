# -*- coding: utf-8 -*-
import json
import logging

from django.http import JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.views.decorators.http import require_http_methods

from passport.decorators import wechat_user_auth
from payment.refundservice import ReFundService
from utils.serializer import DjangoJSONEncoder
from order.orderservice import OrderService

logger = logging.getLogger("django.request")
# Create your views here.

@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_account_balance_list(request,**kwargs):
    # user_id = 1
    user_id = kwargs.get("userid")
    status = request.GET.get("state", 0)
    items = OrderService.get_statement(user_id, status)
    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results":{
            "has_next": False,
            "items": items
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_join_order_list(request,**kwargs):
    user_id = kwargs.get("userid")
    # user_id = 1
    kwargs = {
        "user_id": user_id
    }
    page_size = int(request.GET.get("page_size", 20))
    page_no = int(request.GET.get("page_no", 1))
    list_data, count = OrderService.order_list(page_size, page_no, **kwargs)
    list_data = OrderService.format_jielong_order(list_data)
    # logger.info("get_join_order_list result  %s" % (list_data))
    logger.info("get_join_order_list user_id  %s" % (user_id))
    has_next = False if len(list_data) <= page_size else True
    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "has_next": has_next,
            "items": list_data
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_jielong_order_list(request,**kwargs):
    user_id = kwargs.get("userid")
    jielong_id = request.GET.get("jielong_id",None)
    if not jielong_id:
        result = {
            "meta": {
                "msg": "缺少接龙活动id参数",
                "code": 1
            },
            "results": {}
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    kwargs = {
        "seller_id": user_id,
        "jielong_id":jielong_id
    }
    page_size = int(request.GET.get("page_size", 20))
    page_no = int(request.GET.get("page_no", 1))
    list_data, count = OrderService.order_list(page_size, page_no, **kwargs)
    # list_data = OrderService.format_jielong_order(list_data)
    has_next = False if len(list_data) <= page_size else True
    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "has_next": has_next,
            "items": list_data
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@csrf_exempt
def get_order_detail(request):
    order_id = request.GET.get("order_id", "")
    results = OrderService.order_detail(order_id)
    refund_state = results["refund_state"]
    refund_order = ReFundService.get_format_refund_order(order_id)
    if refund_order != "":
        apply_reason = refund_order["reason"]
    else:
        apply_reason = ""
    if refund_state != "":
        refund_button = False
        if refund_state == "apply_refunding":
            refund_button = True
        results["seller_refund_info"] = {
            "refund_info": results["refund_info"],
            "refund_info_color": results["refund_info_color"],
            "refund_button": refund_button,
            "refund_apply_reason": apply_reason,
            "refund_state": results["refund_state"]

        }
    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": results
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@wechat_user_auth
@csrf_exempt
def order_create(request,**kwargs):
    userid = kwargs.get("userid", None)
    order_dict = json.loads(request.body)
    # req = {
    #     "jielong_id": 1,
    #     "goods": [{
    #         "id": 1,
    #         "sku_desc": "规格",
    #         "product_num": 2
    #     },
    #         {
    #             "id": 2,
    #             "sku_desc": "规格",
    #             "product_num": 3
    #         },
    #     ]
    # }
    jielong_id = order_dict.get("jielong_id")
    goods = order_dict.get("goods")
    spread_user = order_dict.get("spread_user_id")
    o = OrderService(userid)
    try:
        order_id = o.create_order(jielong_id, spread_user, goods)
    except Exception as e:
        msg = str(e)
        result = {
            "meta": {
                "msg": msg,
                "code": 1
            },
            "results": {
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "order_no": order_id
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@wechat_user_auth
@csrf_exempt
def order_cancel(request,**kwargs):
    userid = kwargs.get("userid", None)
    order_dict = json.loads(request.body)
    order_id = order_dict.get("order_id")
    OrderService.cancel_order(order_id)

    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "order_no": order_id
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@transaction.atomic
@wechat_user_auth
@csrf_exempt
def apply_withdraw_cash2(request, **kwargs):
    userid = kwargs.get("userid", 5)
    save_dict = json.loads(request.body)
    money = save_dict.get("money")
    from order.models import WithdrawCash
    user_name = save_dict.get("user_name")
    if not user_name:
        result = {
            "meta": {
                "msg": u"用户实际名不能为空",
                "code": 1
            },
            "results": [],
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    if not money:
        result = {
            "meta": {
                "msg": u"金额不能为空",
                "code": 1
            },
            "results": [],
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    from decimal import Decimal
    money = Decimal(money)
    if money < Decimal("1"):
        result = {
            "meta": {
                "msg": u"申请金额必须大于等于1",
                "code": 1
            },
            "results": [],
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    withdraw_cashs = WithdrawCash.objects.filter(user_id=userid).filter(status=0)
    if withdraw_cashs:
        result = {
            "meta": {
                "msg": u"您有一笔提现正在处理中，不能再次发起提现",
                "code": 1
            },
            "results": [],
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    statements = OrderService.get_balance(userid)
    if not statements:
        result = {
            "meta": {
                "msg": u"提现失败，稍后重试或联系客服",
                "code": 1
            },
            "results": [],
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    if statements:
        balancea = statements
        from passport.models import PassportUser
        user = PassportUser.objects.get(id=userid)
        we_user = user.wechatuser
        import time
        out_trade_no = str(int(time.time() * 1000))

        if balancea < money:
            result = {
                "meta": {
                    "msg": u"提现失败，稍后重试或联系客服",
                    "code": 1
                },
                "results": [],
            }
            return JsonResponse(result, encoder=DjangoJSONEncoder)
        cash_dict = {
            "user_id": userid,
            "user_name": user_name,
            "money": money,
            "open_id": we_user.openid,
            "order_num": out_trade_no,
        }
        # is_send
        # ready_send = WithdrawCash.objects.filter(user_id=userid, status=2).order_by("-update_time")[:1]
        # if ready_send:
        #     result_model = ready_send[0]
        #     out_trade_no = result_model.order_num
        # else:
        #     cash_dict["order_num"] = out_trade_no
        result_model = WithdrawCash.objects.create(**cash_dict)
        from payment.wechartpay import WechartWithdrawCash
        wechart_cash = WechartWithdrawCash()
        wechart_cash.out_trade_no = out_trade_no
        result_json = wechart_cash.withdraw_cash(we_user.openid, money, user_name)
        if result_json.get("result_code", "") == "SUCCESS":
            result_model.payment_no = result_json.get("payment_no", "")
            result_model.status = 1
            result_model.save()
            balance = OrderService.cash_statement(userid, money)
            result = {
                "meta": {
                    "msg": "",
                    "code": 0
                },
                "results": {"balance": balance}
            }
        else:
            # result_model.payment_no = result_json.get("payment_no", "")
            result_model.status = 2
            result_model.remark = result_json.get("err_code_des", "")
            result_model.save()
            result = {
                "meta": {
                    "msg": wechart_cash.check_withdraw_cash_err_des(result_json.get("err_code_des", "")),
                    "code": 40002
                },
                "results": {}
            }
            logger.info("apply_withdraw_cash2 result %s;wx_result_json:%s" % (result,result_json))

    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def withdraw_cash_list(request,**kwargs):
    userid = kwargs.get("userid", None)
    from .models import WithdrawCash
    from payment.wechartpay import utc2local
    cahshes = WithdrawCash.objects.filter(user_id=userid, status=1).order_by("-update_time")
    items = []
    for cahshe in cahshes:
        cash_dict = {
            "price_info": "团购提现 + %.2f" % cahshe.money,
            "date_info": utc2local(cahshe.create_time).strftime("%Y-%m-%d %H:%M:%S"),
            "order_info": "交易成功"
        }
        items.append(cash_dict)

    # result = {
    #     "meta": {
    #         "msg": "",
    #         "code": 1
    #     },
    #     "results": {
    #         "has_next":False,
    #         "items":[
    #         {
    #             "price_info": "接龙提现 + 10",
    #             "date_info": "2018-07-01 12:00:00",
    #             "order_info": "交易成功"
    #         },
    #         {
    #             "price_info": "接龙提现 + 20",
    #             "date_info": "2018-07-02 12:00:00",
    #             "order_info": "交易成功"
    #         }
    #     ]
    # }
    # }

    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "has_next":False,
            "items": items
    }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@transaction.atomic
@wechat_user_auth
@csrf_exempt
def update_commit(request, **kwargs):
    userid = kwargs.get("userid", None)
    order_dict = json.loads(request.body)
    order_id = order_dict.get("order_id")
    order_type = order_dict.get("type", "buyer")
    OrderService.update_remark(order_id, order_dict.get("content", ""), order_type)

    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)

@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_delivery_order_list(request,**kwargs):
    user_id = kwargs.get("userid")
    jielong_id = request.GET.get("jielong_id",None)
    if not jielong_id:
        result = {
            "meta": {
                "msg": "缺少接龙活动id参数",
                "code": 1
            },
            "results": {}
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    kwargs = {
        "seller_id": user_id,
        "jielong_id":jielong_id
    }
    page_size = int(request.GET.get("page_size", 500))
    page_no = int(request.GET.get("page_no", 1))
    list_data, count = OrderService.order_list(page_size, page_no, **kwargs)
    has_next = False if len(list_data) <= page_size else True

    delivery = []
    if len(list_data) > 0:
        for o in list_data:
            order_id = o["trade_id"]
            order_detail = OrderService.order_detail(order_id = order_id)
            receiver = order_detail["address"]["receiver"]
            tel =  order_detail["address"]["tel"]
            address =  order_detail["address"]["address"]
            goods = order_detail["goods"]
            if len(goods) > 0:
                for g in goods:
                    title = g["title"]
                    buy_num = g["buy_num"]
                    delivery_info = "%s。%s。%s。%s * %s " % (receiver,tel,address,title,buy_num)
                    delivery.append(delivery_info)
            else:
                continue
        delivery_info = "\n".join(delivery)
        result = {
            "meta": {
                "msg": "",
                "code": 0
            },
            "results": {
                # "order_data":"姓名,电话,地址,商品名称,商品数量\n姓名,电话,地址,商品名称,商品数量"
                "order_data":delivery_info
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    else:
        result = {
            "meta": {
                "msg": "",
                "code": 0
            },
            "results": {
                }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_order_copy_info(request,**kwargs):
    order_id = request.GET.get("order_id",None)
    if not order_id:
        result = {
            "meta": {
                "msg": "缺少订单id参数",
                "code": 1
            },
            "results": {}
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)


    delivery = []
    order_detail = OrderService.order_detail(order_id = order_id)
    receiver = order_detail["address"]["receiver"]
    tel =  order_detail["address"]["tel"]
    address =  order_detail["address"]["address"]
    goods = order_detail["goods"]
    if len(goods) > 0:
        for g in goods:
            title = g["title"]
            buy_num = g["buy_num"]
            delivery_info = "%s。%s。%s。%s * %s " % (receiver,tel,address,title,buy_num)
            delivery.append(delivery_info)
    delivery_info = "\n".join(delivery)
    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            # "order_data":"姓名,电话,地址,商品名称,商品数量\n姓名,电话,地址,商品名称,商品数量"
            "order_data":delivery_info
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_refund_order_count(request,**kwargs):
    user_id = kwargs.get("userid")
    refund_state = request.GET.get("state", "")
    results = OrderService.refund_order_list(refund_state=refund_state, seller_id=user_id)
    result = {
        "meta":{
            "msg":"",
            "code":0
        },
        "results":{
            "refund_order_count": results[1]
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_refund_order_list(request, **kwargs):
    user_id = kwargs.get("userid")
    page_size = int(request.GET.get("page_size", 20))
    page_no = int(request.GET.get("page_no", 1))
    refund_state = request.GET.get("state", "")
    list_data, count = OrderService.refund_order_list(page_size, page_no, refund_state, seller_id=user_id)
    has_next = False if len(list_data) <= page_size else True
    result = {
        "meta": {
            "msg": "",
            "code": 0,
            "count": count,
        },
        "results": {
            "has_next": has_next,
            "items": list_data
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@wechat_user_auth
@csrf_exempt
def refund_apply(request,**kwargs):
    user_id = kwargs.get("userid")
    from payment.refundservice import ReFundService
    param_dict = json.loads(request.body)
    # param_dict = {
    #     "order_id":100000300006,
    #     "order_price":100,
    #     "apply_reason":""
    # }
    if "order_id" not in param_dict or "apply_reason" not in param_dict:
        result = {
            "meta":{
                "msg":"API请求参数错误/缺少",
                "code":90001
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    results = ReFundService.apply_refund(user_id, param_dict.get("order_id"), param_dict.get("apply_reason", ""))
    result = {
        "meta":{
            "msg": results[1],
            "code": results[0]
        },
        "results": results[2]
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@wechat_user_auth
@csrf_exempt
def refund_refuse(request,**kwargs):
    user_id = kwargs.get("userid")
    from payment.refundservice import ReFundService
    param_dict = json.loads(request.body)
    # param_dict = {
    #     "order_id":100000300006,
    #     "order_price":100,
    #     "apply_reason":""
    # }
    results = ReFundService.disagree_refund(user_id, param_dict.get("order_id"), param_dict.get("apply_reason", ""))
    result = {
        "meta": {
            "msg": results[1],
            "code": results[0]
        },
        "results": results[2]
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@wechat_user_auth
@csrf_exempt
def refund_agree(request,**kwargs):
    user_id = kwargs.get("userid")
    from payment.refundservice import ReFundService
    param_dict = json.loads(request.body)
    # param_dict = {
    #     "order_id":100000300006,
    #     "order_price":100,
    #     "apply_reason":""
    # }
    results = ReFundService.agree_refund(user_id, param_dict.get("order_id"))
    result = {
        "meta": {
            "msg": results[1],
            "code": results[0]
        },
        "results": results[2]
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)