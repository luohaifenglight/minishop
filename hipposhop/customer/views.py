# -*- coding: utf-8 -*-
import json
import logging
import time
from django.http import JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Q

from customer.models import ShareUserRelation, JieLongUserRelation, JieLongSpreadUserRelation
from promotions import jielong_service
from utils.pageinfo import Pagination
from utils.serializer import DjangoJSONEncoder
from utils.date_util import UtilDateTime
from order.orderservice import OrderService
from passport.models import PassportUser, WechatUser
from passport.decorators import wechat_user_auth
from promotions.jielong_service import get_time_span, get_browse_nums_by_spreaduser
from promotions.models import JieLong
from customer.customer_service import CustomerService
from report.order_report import OrderReport
from report.report_util import ReportUtil

logger = logging.getLogger('django.request')


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_customer_info_index(request, **kwargs):
    """
    个人中心--首页
    :param request:
    :return:
    """
    user_id = kwargs.get("userid")
    kwargs = {
        "user_id": user_id,
        "other_query": ~Q(seller_id=user_id),
    }
    logger.info("customer index, kwargs: %s" % kwargs)
    _, fans = CustomerService.get_my_fans_by_user_id(user_id)
    _, follows = CustomerService.get_my_follows(**kwargs)
    spreaders = JieLongSpreadUserRelation.objects.filter(status=1, invite_sponsor_id=user_id).count()
    balance = OrderService.get_balance(user_id)
    _, apply_refunding = OrderService.refund_order_list(refund_state="apply_refunding", seller_id=user_id)

    result = {
        "meta": {
            "msg": "success",
            "code": 0
        },
        "results": {
            "follow": follows,
            "fans": fans,
            "spreader": spreaders,
            "balance": "%s" % balance,
            "apply_refunding": apply_refunding,
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_my_join_jielong_list(request,**kwargs):
    user_id = kwargs.get("userid")
    pagination = Pagination(request)
    result = jielong_service.get_join_jielong_order_by_user_id(user_id,pagination.page_no,pagination.page_size)
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_my_fans_list(request,**kwargs):
    """
    个人中心--我的粉丝
    :param request:
    :return:
    """
    user_id = kwargs.get("userid")
    pagination = Pagination(request)
    items, count = CustomerService.get_my_fans_by_user_id(user_id, pagination=pagination)
    if pagination.end >= count:
        has_next = False
    else:
        has_next = True

    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "count_info": "共拥有粉丝%s人" % count,
            "has_next": has_next,
            "items": items
        }
    }

    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
# @cache_control(max_age=30)
def get_my_follows_list(request, **kwargs):
    """
    个人中心: 我的关注
    :param request:
    :param kwargs:
    :return:
    """
    user_id = kwargs.get("userid")

    pagination = Pagination(request)
    kwargs = {
        "user_id": user_id,
        "other_query": ~Q(seller_id=user_id),
        "pagination": pagination
    }
    start, end = pagination.start, pagination.end
    follows, count = CustomerService.get_my_follows(**kwargs)
    result, items, has_next = {}, [], False
    if follows:
        if count > end:
            has_next = True
        for follow in follows:
            items_dict = {}
            p_user = PassportUser.objects.get(id=follow)
            items_dict["nick"] = jielong_service.get_covert_user_nickname(follow, p_user.wechatuser.nickname)
            items_dict["avatar_url"] = jielong_service.covert_avatar_url(p_user.wechatuser.avatar_url)
            items.append(items_dict)
    result = {
        "meta": {
            "msg": "success",
            "code": 0
        },
        "results": {
            "count_info": "共关注了%s人" % count,
            "has_next": has_next,
            "items": items
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_my_spread_jielong_list(request,**kwargs):
    user_id = kwargs.get("userid")
    pagination = Pagination(request)
    start = pagination.start
    end = pagination.end
    jielong_list = jielong_service.get_jielong_list_by_spread_user(user_id, start, end)
    return JsonResponse(jielong_list, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
# @cache_control(max_age=30)
def get_share_join_user_list(request, **kwargs):
    """
    我的分享:参与的人
    :param request: jielong_id
    :return:
    """
    user_id = kwargs.get("userid")
    pagination = Pagination(request)
    jielong_id = request.GET.get("jielong_id", None)

    if not jielong_id:
        code, msg = 2, "缺少参数"
        result = {"meta": {"msg": msg, "code": code}, "results": {}}
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    jielong_id = int(jielong_id)
    jielong = JieLong.objects.get(id=jielong_id)
    inviter_id = jielong.passport_user_id
    spreader_ids, _ = CustomerService.get_my_spreaders_by_inviter_id(inviter_id, pagination=pagination, is_all=True)

    results, items, is_spreader = {}, [], False
    if user_id in spreader_ids:
        is_spreader = True
    logger.info("share_join_users,user_id:%s; jielong_id: %s; inviter_id: inviter_id: %s; is_spreader: %s" % (user_id, jielong_id, inviter_id, is_spreader))

    order_list, count = OrderService.order_list(page_no=pagination.page_no, page_size=pagination.page_size, spread_user_id=user_id, jielong_id=jielong_id)
    commission_info = OrderService.count_data(spread_user_id=user_id, jielong_id=jielong_id)
    total_commssion_price = commission_info["order_commission_price"]
    total_order_num = commission_info["order_num"]
    has_next = False if len(order_list) <= pagination.page_size else True

    if len(order_list) > 0:
        for o in order_list:
            goods_info = []
            goods = o["goods"]
            if len(goods) > 0:
                for g in goods:
                    g_info = "%s(%s) x%s" % (g["title"], g["sku_desc"], g["buy_num"])
                    goods_info.append(g_info)

            items_dict = {
                    "nick": jielong_service.get_covert_user_nickname(o["user_id"], o["nickname"]),
                    "avatar_url": jielong_service.covert_avatar_url(o["avatar_url"]),
                    "create_time": get_time_span(o["order_time"].strftime("%Y-%m-%d %H:%M:%S")),
                    "goods_info": goods_info,
                }
            if is_spreader:
                items_dict["commission_info"] = "奖励%s元" % o["reward_price"]
            items.append(items_dict)

    results = {
        "has_next": has_next,
        "subTitle": "%s人下单" % total_order_num,
        "items": items
    }
    if is_spreader:
        results["total_commission"] = "共获得%s元奖励" % total_commssion_price

    result = {
        "meta": {
            "msg": "success",
            "code": 0,
        },
        "results": results
    }
    logger.info("get_share_join_user_list, results: %s;" % (results))
    return JsonResponse(result, encoder=DjangoJSONEncoder)



@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
# @cache_control(max_age=30)
def get_share_browse_user_list(request, **kwargs):
    """
    我的分享:浏览的人
    :param request:
    :return:
    """
    user_id = kwargs.get("userid")
    jielong_id = request.GET.get("jielong_id", None)
    pagination = Pagination(request)
    start = pagination.start
    end = pagination.end

    results, items, has_next = {}, [], False
    if not jielong_id:
        code, msg = 90001, "缺少参数"
        logger.info("share_browser_list, user_id: %s, code:%s; msg: %s" % (user_id, code, msg))
        result = {"meta": {"msg": msg, "code": code}, "results": results}
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    jielong_id = int(jielong_id)
    share_user_relations = ShareUserRelation.objects.filter(share_user_id=user_id, jielong_id=jielong_id)
    count = share_user_relations.count()
    logger.info("share_browser, jielong_id:%s; count:%s, user_id: %s" % (jielong_id, count, user_id))
    if count > 0:
        share_user_relations = share_user_relations.order_by("-update_time")[start: end]
        if count > end:
            has_next = True
        for share_user_relation in share_user_relations:
            items_dict = {}
            browse_user = share_user_relation.browse_user
            items_dict["avatar_url"] = jielong_service.covert_avatar_url(browse_user.wechatuser.avatar_url)
            items_dict["nick"] = jielong_service.get_covert_user_nickname(browse_user.id, browse_user.wechatuser.nickname)
            items_dict["create_time"] = get_time_span(UtilDateTime.utc2local(share_user_relation.update_time))
            items.append(items_dict)
    results["has_next"] = has_next
    results["items"] = items
    results["subTitle"] = "%s人浏览" % count
    code, msg = 0, "success"

    result = {
        "meta": {
            "msg": msg,
            "code": code
        },
        "results": results
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_spread_tab(request, **kwargs):
    """
    申请人及推广人tab
    :param request:
    :param kwargs:
    :return:
    """
    user_id = kwargs.get("userid")
    apply_count = JieLongSpreadUserRelation.objects.filter(invite_sponsor_id=user_id, status=0).count()
    spread_count = JieLongSpreadUserRelation.objects.filter(invite_sponsor_id=user_id, status=1).count()

    result = {
        "meta": {
            "code": 0,
            "msg": "success",
        },
        "results": {
            "apply_count": apply_count,
            "spread_count": spread_count,
            "inviter_id": user_id,
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_spread_apply_user_list(request, **kwargs):
    """
    我的推广者--申请者列表
    :param request:
    :return:
    """
    user_id = kwargs.get("userid")
    pagination = Pagination(request)
    start = pagination.start
    end = pagination.end

    results, items, has_next = {}, [], False
    user_relations = JieLongSpreadUserRelation.objects.filter(invite_sponsor_id=user_id, status=0)
    count = user_relations.count()
    logger.info("applying_users, user_id: %s; count: %s" % (user_id, count))
    if count > 0:
        user_relations = user_relations.order_by("-update_time")[start: end]
        if count > end:
            has_next = True

        for user_relation in user_relations:
            items_dict = {}
            items_dict["id"] = user_relation.passport_user.id
            items_dict["nick"] = user_relation.passport_user.wechatuser.nickname
            items_dict["avatar_url"] = user_relation.passport_user.wechatuser.avatar_url
            items_dict["wechat_info"] = "微信 : %s" % user_relation.wechat_no
            items_dict["content"] = user_relation.apply_reason
            items_dict["create_time"] = "申请时间 %s" % UtilDateTime.utc2local(user_relation.update_time)
            items.append(items_dict)
    results["count"] = count
    results["has_next"] = has_next
    results["items"] = items
    code, msg = 0, "success"
    result = {
        "meta": {
            "msg": msg,
            "code": code
        },
        "results": results
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_spread_user_list(request, **kwargs):
    """
    我的推广者--推广人列表
    :param request:
    :return:
    """
    user_id = kwargs.get("userid")
    pagination = Pagination(request)
    start = pagination.start
    end = pagination.end
    try:
        results, items, has_next = {}, [], False
        user_relations = JieLongSpreadUserRelation.objects.filter(invite_sponsor_id=user_id, status=1)
        count = user_relations.count()
        logger.info("spreader_list, user_id: %s; count: %s" % (user_id, count))
        if count > 0:
            user_relations = user_relations.order_by("-update_time")[start:end]
            if count > end:
                has_next = True
            for user_relation in user_relations:
                items_dict = {}
                order_num_result = OrderService.total_commission_price(seller_id=user_id, spread_user_id=user_relation.passport_user_id)
                o_list, order_count = OrderService.order_list(page_size=20, page_no=1, seller_id=user_id, spread_user_id=user_relation.passport_user_id)

                items_dict["id"] = user_relation.passport_user.id
                items_dict["nick"] = jielong_service.get_covert_user_nickname(user_relation.passport_user_id, user_relation.passport_user.wechatuser.nickname)
                items_dict["avatar_url"] = jielong_service.covert_avatar_url(user_relation.passport_user.wechatuser.avatar_url)
                items_dict["status"] = user_relation.status
                items_dict["commission_info"] = "共推广%s单，收入%s元" % (order_count, order_num_result)
                items.append(items_dict)
        results["count"] = count
        results["items"] = items
        results["has_next"] = has_next
        code, msg = 0, "success"
        logger.info("get_spread_user_list: result:%s" % (results))
    except Exception as e:
        print(e)
        logger.info("get_spread_user_list: error:%s" % (e))
        code, msg = 90100, "服务器错误"
        results = {}
    result = {
        "meta": {
            "msg": msg,
            "code": code
        },
        "results": results
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@csrf_exempt
def browse_jielong(request,**kwargs):
    param_dict = json.loads(request.body)
    user_id = param_dict.get('user_id')
    share_user_id = param_dict.get('share_user_id')
    jielong_id = param_dict.get('jielong_id')

    logger.info(
        "browse_jielong param: browse_user_id:%s;share_user:%s;jielong_id:%s" % (user_id, share_user_id, jielong_id))

    if not user_id or not share_user_id or not jielong_id:
        result = {
            "meta": {
                "msg": "缺少参数",
                "code": 90001
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    share_user_id = int(share_user_id)
    jielong_id = int(jielong_id)
    try:
        shares = ShareUserRelation.objects.get(browse_user_id=user_id,share_user_id=share_user_id,jielong_id=jielong_id)
        browse_num = shares.browse_num + 1
    except ShareUserRelation.DoesNotExist:
        browse_num = 1
    share_dict = {
        "browse_num":browse_num
    }

    shares = ShareUserRelation.objects.update_or_create(browse_user_id=user_id, jielong_id=jielong_id, share_user_id=share_user_id, defaults=share_dict)

    if shares:
        share = shares[0]
        jielong_browse_num = share.jielong.browse_num
        share.jielong.browse_num = jielong_browse_num + 1
        share.jielong.save()
        result = {
            "meta": {
                "msg": "",
                "code": 0
            }
        }
    else:
        result = {
            "meta": {
                "msg": "浏览分享统计信息上传失败",
                "code": 90002
            }
        }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET", "POST"])
@wechat_user_auth
@csrf_exempt
def apply_to_spreader(request, **kwargs):
    user_id = kwargs.get("userid")
    results = {}
    code, msg = 0, "success"

    if request.method == "GET":
        inviter_id = request.GET.get("inviter_id", None)
        logger.info("apply_to_spreader,method: %s, user_id: %s, inviter_id:%s" % (request.method, user_id, inviter_id))
        if inviter_id:
            we_user = WechatUser.objects.get(passport_user_id=int(inviter_id))
            avatar_url = we_user.avatar_url
            nick = we_user.nickname
            results = {"id": inviter_id, "nick": nick, "avatar_url": avatar_url}
        else:
            code, msg = 1, "缺少参数"
        result = {
            "meta": {
                "msg": msg,
                "code": code
            },
            "results": results
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    elif request.method == "POST":
        try:
            param_dict = json.loads(request.body.decode("utf-8"))
            inviter_id = int(param_dict.get('inviter_id'))
            wechat_no = param_dict.get("wechat_no")
            content = param_dict.get("content")

            logger.info("apply_to_spreader,method: %s, user_id: %s, param_dict:%s" % (request.method, user_id, param_dict))
            if inviter_id != user_id:
                jielong_users = JieLongSpreadUserRelation.objects.filter(invite_sponsor_id=inviter_id, passport_user_id=user_id)
                if jielong_users and (jielong_users[0].status in (0, 1)):
                    code, msg = 90003, "已经申请过"
                else:
                    jielong_relation = JieLongSpreadUserRelation.objects.update_or_create(
                        invite_sponsor_id=inviter_id, passport_user_id=user_id, defaults={
                            "wechat_no": wechat_no,
                            "status": 0
                        }
                    )
                    code, msg = 0, "success"
            else:
                code, msg = 90004, "自身不能成为推广人"
        except Exception as e:
            logger.info("apply_to_spreader, Exception: %s" % e)
            code, msg = 90005, "申请推广人信息上传失败"
        result = {
            "meta": {
                "msg": msg,
                "code": code
            },
            "results": results
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@wechat_user_auth
@csrf_exempt
def update_is_spreader(request, **kwargs):
    """
    :param request:
    :param kwargs:  status, spreader_id
    :return:
    """
    user_id = kwargs.get("userid")
    param_dict = json.loads(request.body.decode("utf-8"))
    status = int(param_dict.get("status"))
    spreader_id = int(param_dict.get("spreader_id"))
    logger.info("update_is_spreader, user_id: %s; param_dict: %s" % (user_id, param_dict))
    if spreader_id and status not in (1, 2, 3):
        result = {"meta": {"code": 90001, "msg": "缺少参数"}, "results": {}}
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    try:
        user = JieLongSpreadUserRelation.objects.get(invite_sponsor_id=user_id, passport_user_id=spreader_id)
        user.status = status
        user.save()
        code, msg = 0, "操作成功"
    except JieLongSpreadUserRelation.DoesNotExist:
        logger.info("update_is_spreader, Exception, user_id: %s, passport_user_id: %s" % (user_id, spreader_id))
        code, msg = 20004, "未找到匹配的用户"
    result = {
        "meta": {
            "msg": msg,
            "code": code
        },
        "results": {}
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_jielong_statistics(request, **kwargs):
    """
    数据统计-接龙统计
    :param request: activity_id,
    :return:
    """
    user_id = kwargs.get("userid")
    jielong_id = request.GET.get("jielong_id", None)
    if not jielong_id:
        code, msg = 90001, "缺少参数"
        result = {"meta": {"msg": msg, "code": code}, "results": {}}
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    jielong_id = int(request.GET.get("jielong_id"))
    results = {}
    try:
        kwargs = {"jielong_id": jielong_id, "seller_id": user_id}
        jielong_json = OrderService.count_data(**kwargs)
        jielong = JieLong.objects.get(id=jielong_id)
        browse_num = jielong.browse_num
        share_num = ShareUserRelation.objects.filter(jielong_id=jielong_id, share_user_id=user_id).count()
        if browse_num == 0:
            rates = 0
        else:
            rates = round(jielong_json["order_num"]/browse_num*100, 1)
        results = {
            "sequence": [
                {"label": "团购人数", "value": "%s" % jielong_json.get("order_user_num", 0)},
                {"label": "团购订单数", "value": "%s" % jielong_json.get("order_num", 0)},
                {"label": "浏览人数", "value": "%s" % browse_num},
                {"label": "分享人数", "value": "%s" % share_num},
                {"label": "转化率", "value": "%s" % rates + "%"}
            ],
            "income": [
                {"label": "订单收入", "value": "%s元" % jielong_json.get("order_total_price", 0)},
                {"label": "佣金支出", "value": "%s元" % jielong_json.get("order_commission_price", 0)},
                # {"label": "佣金支出", "value": "%s元" % jielong_json.get("order_commission_price", 0)},
                # {"label": "微信支付手续费(0.6%)", "value": "%s元" % jielong_json.get("order_wx_charge", 0)},
                # {"label": "净收入", "value": "%s元" % jielong_json.get("order_net_income", 0)}
            ]
        }
        logger.info("get_jielong_statistics result: %s;jielong_json: %s" % (results,jielong_json))
        code, msg = 0, "success"
    except Exception as e:
        logger.info("share_statictics, Exception: %s,user_id: %s, jielong_id: %s" % (e, user_id, jielong_id))
        code, msg = 90100, "服务器错误"
    result = {
        "meta": {
            "msg": msg,
            "code": code
        },
        "results": results
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_jielong_share_statistics(request, **kwargs):
    """
    数据统计-分享统计
    :param request: jielong_id, is_common
    :return:
    """
    user_id = kwargs.get("userid")
    jielong_id = int(request.GET.get("jielong_id", None))
    is_common = int(request.GET.get("is_common", None))
    if not jielong_id or (is_common not in (1, 0)):
        code, msg = 2, "缺少参数"
        result = {"meta": {"msg": msg, "code": code}, "results": {}}
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    pagination = Pagination(request)
    start, end = pagination.start, pagination.end
    results, items, has_next = {}, [], False
    total_count, total_money, total_commission = 0, 0, 0
    spreaders = JieLongSpreadUserRelation.objects.filter(invite_sponsor_id=user_id, status=1)
    spreaders_ids = [sp.passport_user_id for sp in spreaders]
    logger.info("share_statistics,user_id:%s, jielong_id: %s, is_common: %s" % (user_id, jielong_id, is_common))
    try:
        if not is_common:
            # 推广人
            kwargs = {
                "jielong_id": jielong_id,
                "seller_id": user_id,
                # "other_query": Q(buyer_id__in=spreaders_ids),
                "spread_user_ids": spreaders_ids,
            }

            _, total_count = OrderService.order_list(**kwargs)
            total_money = OrderService.total_order_price(**kwargs)
            total_commission = OrderService.total_commission_price(**kwargs)

            order_users = OrderService.order_queryset(**kwargs)
            if order_users:
                user_ids = order_users.values_list("spread_user_id", flat=True).distinct()
                # user_ids = [u for u in user_ids if u in spreaders_ids]
                logger.info("share_statistics, is_common: %s, user_ids: %s" % (is_common, user_ids))
                count = user_ids.count()
                if count:
                    if count > end:
                        has_next = True
                    user_ids = user_ids[start: end]
                    for u_id in user_ids:
                        _, u_count = OrderService.order_list(page_size=20, page_no=1, jielong_id=jielong_id, spread_user_id=u_id)
                        u_commission = OrderService.total_commission_price(jielong_id=jielong_id, spread_user_id=u_id)
                        we_user = WechatUser.objects.get(passport_user_id=u_id)
                        u_browse = ShareUserRelation.objects.filter(jielong_id=jielong_id, share_user_id=u_id).aggregate(browse=Sum("browse_num"))["browse"] or 0
                        item_dict = {}
                        item_dict["member_id"] = u_id
                        item_dict["imageUrl"] = jielong_service.covert_avatar_url(we_user.avatar_url)
                        item_dict["name"] = jielong_service.get_covert_user_nickname(u_id, we_user.nickname)
                        item_dict["title"] = "邀请%s人浏览，成交%s单，佣金%s元" % (u_browse, u_count, u_commission)
                        items.append(item_dict)
            sub_title = "共推广%s单，交易金额%s元，佣金%s元" % (total_count, total_money, total_commission)
        else:
            # 普通团员
            kwargs = {
                "jielong_id": jielong_id,
                "seller_id": user_id,
                # "other_query": ~Q(buyer_id__in=spreaders_ids),
                "spread_user_id": user_id,
            }

            _, total_count = OrderService.order_list(**kwargs)
            total_money = OrderService.total_order_price(**kwargs)
            order_users = OrderService.order_queryset(**kwargs)
            if order_users:
                user_ids = order_users.values_list("buyer_id", flat=True).distinct()
                logger.info("share_statistics, is_common: %s, user_ids: %s" % (is_common, user_ids))
                count = user_ids.count()
                if count:
                    if count > end:
                        has_next = True
                    user_ids = user_ids[start: end]
                    for u_id in user_ids:
                        _, u_count = OrderService.order_list(page_size=20, page_no=1, jielong_id=jielong_id, user_id=u_id)
                        we_user = WechatUser.objects.get(passport_user_id=u_id)
                        u_browse = ShareUserRelation.objects.filter(jielong_id=jielong_id, share_user_id=u_id).aggregate(browse=Sum("browse_num"))["browse"] or 0
                        item_dict = {}
                        item_dict["member_id"] = u_id
                        item_dict["imageUrl"] = jielong_service.covert_avatar_url(we_user.avatar_url)
                        item_dict["name"] = jielong_service.get_covert_user_nickname(u_id, we_user.nickname)
                        item_dict["title"] = "邀请%s人浏览，成交%s单" % (u_browse, u_count)
                        items.append(item_dict)
            sub_title = "共成交%s单，交易额%s元" % (total_count, total_money)
        results["subTitle"] = sub_title
        results["items"] = items
        code, msg = 0, "success"
    except Exception as e:
        logger.info("share_statistics, Exception: %s" % e)
        code, msg = 90100, "服务器错误"
    results["has_next"] = has_next
    result = {
        "meta": {
            "msg": msg,
            "code": code
        },
        "results": results
    }

    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@csrf_exempt
def update_my_fans_after_order(request):
    """
    个人中心-更新我的粉丝
    :param request: jielong_id
    :param kwargs:
    :return:
    """
    user_id = int(request.GET.get("user_id", None))
    jielong_id = request.GET.get("jielong_id", None)
    code, msg = 0, "success"
    if jielong_id and user_id:
        jielong = JieLong.objects.get(id=jielong_id)
        if jielong.passport_user_id != user_id:
            obj, created = JieLongUserRelation.objects.update_or_create(
                passport_user_id=user_id, jielong_id=jielong_id, defaults={
                    "is_attention": 0
                }
            )
        else:
            code, msg = 0, "自己不能成为自己的粉丝"

    else:
        code, msg = 90001, "缺少参数"
    result = {"meta": {"msg": msg, "code": code}, "results": {}}
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@wechat_user_auth
@csrf_exempt
def get_jielong_statistics_order_list(request, **kwargs):
    """
    数据统计-分享统计-查看推广详情
    :param request:
    :param kwargs: jielong_id, member_id, is_common
    :return:
    """
    user_id = kwargs.get("userid")
    jielong_id = int(request.GET.get("jielong_id", None))
    member_id = int(request.GET.get("member_id", None))
    is_common = int(request.GET.get("is_common", None))

    if not jielong_id or (is_common not in (1, 0)) or (not member_id):
        code, msg = 90001, "缺少参数"
        result = {"meta": {"msg": msg, "code": code}, "results": {}}
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    results, items, has_next = {}, [], False
    pagination = Pagination(request)
    start, end = pagination.start,  pagination.end

    logger.info("jielong_statistics, user_id: %s; jielong_id:%s;member_id: %s;is_common: %s" % (user_id, jielong_id, member_id, is_common))
    if is_common:
        # 普通团员
        kwargs = {"user_id": member_id, "jielong_id": jielong_id, "seller_id": user_id}
        order_list, count = OrderService.order_list(page_size=pagination.page_size, page_no=pagination.page_no, **kwargs)
        total_order_price = OrderService.total_order_price(**kwargs)

        if order_list:
            if count > end:
                has_next = True

            for order in order_list:
                item_dict = {}

                item_dict["nick"] = jielong_service.get_covert_user_nickname(order["user_id"], order["nickname"])
                item_dict["avatar_url"] = jielong_service.covert_avatar_url(order["avatar_url"])
                item_dict["create_time"] = get_time_span((order["order_time"].strftime("%Y-%m-%d %H:%M:%S")))
                item_dict["goods_info"] = ["%s ×%s  %s元" % (g["title"], g["buy_num"], g["price"]) for g in order["goods"]]
                items.append(item_dict)
        results["subTitle"] = "共成交%s单，交易额%s元" % (count, total_order_price)
    else:
        # 推广人
        kwargs = {"spread_user_id": member_id, "jielong_id": jielong_id, "seller_id": user_id}
        order_list, count = OrderService.order_list(page_size=pagination.page_size, page_no=pagination.page_no, **kwargs)
        total_commission_price = OrderService.total_commission_price(**kwargs)
        total_order_price = OrderService.total_order_price(**kwargs)
        browse_nums = get_browse_nums_by_spreaduser(jielong_id, member_id)

        if order_list:
            if count > end:
                has_next = True
            for order in order_list:
                item_dict = {}
                item_dict["nick"] = jielong_service.get_covert_user_nickname(order["user_id"], order["nickname"])
                item_dict["avatar_url"] = jielong_service.covert_avatar_url(order["avatar_url"])
                item_dict["create_time"] = get_time_span(order["order_time"].strftime("%Y-%m-%d %H:%M:%S"))
                item_dict["goods_info"] = ["%s ×%s  %s元" % (g["title"], g["buy_num"], g["price"]) for g in order["goods"]]
                item_dict["commission_info"] = "奖励%s元" % order["reward_price"]
                items.append(item_dict)

        results["subTitle"] = "邀请%s人浏览，成交%s单，佣金%s元，交易额%s元" % (browse_nums, count, total_commission_price, total_order_price)
    results["has_next"] = has_next
    results["items"] = items
    code, msg = 0, "success"
    result = {"meta": {"msg": msg, "code": code}, "results": results}

    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@csrf_exempt
def get_my_join_jielong_detail(request):
    order_id = request.GET.get("order_id", "")
    results = OrderService.order_detail(order_id)
    if results:
        jielong_id = results["activity_id"]
        jielong = JieLong.objects.get(id=jielong_id)
        p_nickname = jielong.passport_user.wechatuser.nickname
        p_avatar_url =jielong.passport_user.wechatuser.avatar_url
        wechat_no = jielong.wechat_no
        results["nickname"] = p_nickname
        results["avatar_url"] = p_avatar_url
        results["wechat_no"] = wechat_no
        results["time_info"] = "%s发起" % (get_time_span(UtilDateTime.utc2local(jielong.create_time)))
        results["title"] = jielong.title
        results["order_time"] = results["order_time"].strftime("%Y-%m-%d %H:%M:%S")
        results["activity_status"] = jielong_service.get_jielong_status(jielong_id)

    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": results
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
# @wechat_user_auth
@csrf_exempt
def export_orders_send_to_inviter(request):
    jielong_id = request.GET.get("jielong_id", None)
    email = request.GET.get("email", None)
    if not jielong_id or not email:
        code, msg = 90001, "缺少参数"
        result = {"meta": {"msg": msg, "code": code}, "results": {}}
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    jielong_id = int(jielong_id)

    header = [u'订单号',  u'商品名称', u'购买数量', u'订单金额', u'收货人', u'联系电话', u'收货地址', u'买家备注', u'卖家备注']
    header_width = ['5000', '11000', '3000', '3000', '3000',  '4000', '11000', '4000', '4000']
    sheetname = u'团购订单'
    cur_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    jielong_title = jielong_service.get_jielong_info_by_id(jielong_id)
    filename = "%s%s.xls" % (cur_date, jielong_title)

    order_report = OrderReport(filename, sheetname, header, header_width)
    output_filename = order_report.get_jielong_report(jielong_id)

    subject = "%s%s-团购订单" % (cur_date, jielong_title)
    content = "这是您的河马团购订单列表，请查看附件！"
    code, msg = ReportUtil.send_mail(subject=subject, content=content, to_address=[email], attach_file=output_filename)

    logger.info("export_orders_send_email, jielong_id:%s, email:%s, msg:%s, output_filename:%s" %
                (jielong_id, email, msg, output_filename))
    result = {
        "meta": {
            "msg": msg,
            "code": code,
        },
        "results": {}
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


