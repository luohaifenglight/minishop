# -*- coding: utf-8 -*-
import json
import logging
from functools import reduce

from django.http import JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from order.orderservice import OrderService
from passport.decorators import wechat_user_auth
from promotions import jielong_service
from promotions.jielong_service import get_time_span
from promotions.models import JieLong
from utils.date_util import UtilDateTime
from utils.pageinfo import Pagination
from utils.serializer import DjangoJSONEncoder


logger = logging.getLogger("django.request")


# Create your views here.
@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def test(request,**kwargs):
    user_id = kwargs.get("userid")
    result = {
        "meta":{
            "msg":"",
            "code":0
        },
        "userid":user_id
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)

@require_http_methods(["POST"])
@wechat_user_auth
@csrf_exempt
def add_jielong(request,**kwargs):
    user_id = kwargs.get("userid")
    # user_id = 1
    param_dict = json.loads(request.body)

    images = param_dict.get("operation").get("images")
    small_image = " ".join(images)
    jielong_id = param_dict.get("operation").get("id")

    try:
        if not jielong_id or jielong_id == "":
            jielong = JieLong()
            jielong.passport_user_id = user_id
            jielong.title = param_dict.get("operation").get("title")
            jielong.description = param_dict.get("operation").get("info")
            jielong.begin_time = UtilDateTime.timestr_to_datetime(param_dict.get("others").get("start_time"))
            jielong.end_time = UtilDateTime.timestr_to_datetime(param_dict.get("others").get("end_time"))
            jielong.small_images = small_image
            jielong.commission_rate = param_dict.get("others").get("commission")
            jielong.wechat_no = param_dict.get("others").get("wechat_id")
            jielong.is_logistics = param_dict.get("others").get("logistics")
            jielong.save()
            jielong_service.edit_jielong_product(param_dict,jielong.id)
            jielong_id = jielong.id
            logger.info("add_jielong result add-opt:user_id :%s;jielong_id %s" % (user_id, jielong_id))
        else:
            jielong_service.update_jielong_by_id(jielong_id,param_dict)
            jielong_service.edit_jielong_product(param_dict, jielong_id)
            logger.info("add_jielong result update-opt:user_id :%s;jielong_id %s" % (user_id, jielong_id))

        result = {
            "meta": {
                "msg": "",
                "code": 0
            },
            "results":{
                "jielong_id":jielong_id
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    except Exception as e:
        logger.info("add_jielong exception：error_code:30002;error_msg:%s;param %s" % (e, param_dict))
        result = {
            "meta": {
                "msg": e,
                "code": 30002
            },
            "results":{}
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def cancel_jielong(request,**kwargs):
    jielong_id = request.GET.get("jielong_id",None)
    if not jielong_id:
        result = {
            "meta":{
                "msg":"API请求参数错误","code":90001
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    jielong_dict = {
        "status":1
    }

    try:
        jielong = JieLong.objects.update_or_create(id=jielong_id,defaults=jielong_dict)
        result = {
            "meta":{
                "msg":"success","code":0
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    except Exception as e:
        logger.info("cancel_jielong exception：error_code:30004;error_msg:%s;jielong_id %s" % (e, jielong_id))
        result = {
            "meta":{
                "msg":"结束团购活动异常","code":30004
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

@require_http_methods(["GET"])
@csrf_exempt
def query_jielong(request):
    activity_id = request.GET.get("jielong_id", None)
    if not activity_id:
        result = {
            "meta":{
                "msg":"API请求参数错误",
                "code":90001
            },
            "results":{}
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    jielongs = JieLong.objects.filter(id=activity_id)
    if jielongs:
        jielong = jielongs[0]
        result = {
            "meta": {
                "msg": "",
                "code": 0
            },
            "results": {
                "operation": {
                    "id": jielong.id,
                    "title": jielong.title,
                    "info": jielong.description,
                    "images": [sm for sm in jielong.small_images.split(" ")]
                },
                "goods": jielong_service.get_product_list_by_jielong(jielong.id),
                "others": {
                    "end_time": UtilDateTime.utc2local(jielong.end_time),
                    "start_time": UtilDateTime.utc2local(jielong.begin_time),
                    "logistics": jielong.is_logistics,
                    "wechat_id": jielong.wechat_no,
                    "commission": int(jielong.commission_rate)
                }
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    else:
        result = {
            "meta":{
                "msg":"团购活动未找到",
                "code":30001
            },
            "results":{}
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_jielong_list(request,**kwargs):
    pagination = Pagination(request)
    start = pagination.start
    end = pagination.end
    user_id = kwargs.get("userid",None)
    ##############################
    c_ids,p_ids,m_ids = jielong_service.get_jielong_ids(user_id)

    jielongs = JieLong.objects.filter(id__in=m_ids).order_by("-display_order","-create_time")[start:end]
    # count = jielongs.count()
    count = len(m_ids)
    ##############################
    # jielongs = jielongs[start:end]
    if count > end:
        has_next = True
    else:
        has_next = False
    jielong = []
    if jielongs:
        for j in jielongs:
            order_list,count = OrderService.order_list(page_no=1, page_size=5, jielong_id=j.id)
            jielong_detail = {
                "id":j.id,
                "avatar_url":jielong_service.covert_avatar_url(j.passport_user.wechatuser.avatar_url),
                "nickname":jielong_service.get_covert_user_nickname(j.passport_user.id,j.passport_user.wechatuser.nickname),
                "time_info":"%s发起 , %s人看过 , %s人参与" % (get_time_span(UtilDateTime.utc2local(j.create_time)),j.browse_num,count),
                "title":j.title,
                "thumb_images":[sm for sm in j.small_images.split(" ")] if j.small_images else [],
                "status":jielong_service.get_jielong_status(j.id),
                "details":jielong_service.format_index_jielong_order(order_list),
                "label":jielong_service.get_jielong_label(j.id,c_ids,p_ids)
            }
            jielong.append(jielong_detail)

    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results":{
            "has_next":has_next,
            "items":jielong
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def jielong_detail(request,**kwargs):
    user_id = kwargs.get("userid")
    activity_id = request.GET.get("jielong_id",None)
    if not activity_id:
        result = {
            "meta":{
                "msg":"API请求参数错误",
                "code":90001
            }
        }
        logger.info("jielong_detail result user_id:%s;jielong_id %s" % (user_id, activity_id))
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    try:
        result = jielong_service.get_jielong_detail(activity_id,user_id)
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    except Exception as e:
        result = {
            "meta":{
                "msg":"活动查询异常",
                "code":30003
            }
        }
        logger.info("jielong_detail exception：error_code:30003;error_msg:%s;jielong_id %s" % (e, activity_id))
        return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@csrf_exempt
def get_jielong_order_list(request):
    jielong_id = request.GET.get("jielong_id",None)
    if not jielong_id:
        result = {
            "meta":{
                "msg":"API请求参数错误",
                "code":90001
            }
        }
        logger.info("get_jielong_order_list result jielong_id %s" % (jielong_id))
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    pagination = Pagination(request)
    order_list, count = OrderService.order_list(page_no=pagination.page_no, page_size=pagination.page_size,jielong_id=jielong_id)
    has_next = False if len(order_list) <= pagination.page_size else True
    orders = []
    if len(order_list) > 0:
        index = len(order_list)
        for o in order_list:
            goods_info = []
            goods = o["goods"]
            if len(goods):
                for g in goods:
                    g_info = "%s(%s元) x %s" % (g["title"],g["price"],g["buy_num"])
                    goods_info.append(g_info)
            item = {
                "index": index,
                "nick":jielong_service.get_covert_user_nickname(o["user_id"],o["nickname"]),
                "avatar_url":jielong_service.covert_avatar_url(o["avatar_url"]),
                "create_time":get_time_span(o["order_time"].strftime("%Y-%m-%d %H:%M:%S")),
                "order_info": "已支付%s元" % (o["order_price"]),
                "specifications_info":goods_info
            }
            orders.append(item)
            index -= 1

    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "has_next": has_next,
            "items":orders
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_my_jielong_order_list(request,**kwargs):
    user_id = kwargs.get("userid")
    jielong_id = request.GET.get("jielong_id",None)
    if not jielong_id:
        result = {
            "meta":{
                "msg":"活动id不能为空",
                "code":1
            }
        }
        logger.info("jielong_detail result user_id:%s;jielong_id %s" % (user_id, jielong_id))
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    pagination = Pagination(request)
    order_list, count = OrderService.order_list(page_no=pagination.page_no, page_size=pagination.page_size,user_id=user_id,jielong_id=jielong_id)
    has_next = False if len(order_list) <= pagination.page_size else True

    orders = []
    if len(order_list) > 0:
        index = len(order_list)
        for o in order_list:
            goods_info = []
            goods = o["goods"]
            if len(goods):
                for g in goods:
                    g_info = "%s(%s元) x %s" % (g["title"],g["price"],g["buy_num"])
                    goods_info.append(g_info)
            item = {
                "index": index,
                "nick":jielong_service.get_covert_user_nickname(o["user_id"],o["nickname"]),
                "avatar_url":jielong_service.covert_avatar_url(o["avatar_url"]),
                "create_time":get_time_span(o["order_time"].strftime("%Y-%m-%d %H:%M:%S")),
                "order_info": "已支付%s元" % (o["order_price"]),
                "specifications_info":goods_info,
                "refund_info": o["refund_info"],
                "refund_state": o["refund_state"],
                "refund_info_color": o["refund_info_color"],
                "trade_id":o["trade_id"]
            }
            orders.append(item)
            index -= 1

    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "has_next": has_next,
            "items":orders
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


