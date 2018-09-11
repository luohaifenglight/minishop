# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from passport import wechat_service
from passport.models import Session
from utils.serializer import DjangoJSONEncoder


# from passport.decorators import user_auth


@require_http_methods(["GET"])
@csrf_exempt
def get_jscode2session(request, **kwargs):
    """
    用于客户端绑定微信账号, 客户端完成微信授权后调用该接口
    :param request:
    :param kwargs:
    :return:
    """
    code = request.GET.get("code", None)
    if not code:
        result = {
            "meta": {
                "msg": "缺少参数code",
                "code": 1
            },
            "results": {
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    try:
        result_json = wechat_service.wechat_jscode2session(code)
    except Exception as e:
        error_message = '微信接口请求失败'
        print(e)
        result = {
            "meta": {
                "msg": error_message,
                "code": 40001
            },
            "results": {
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    error_info = wechat_service.get_wechat_error_info(result_json)
    if error_info:
        return JsonResponse(error_info, encoder=DjangoJSONEncoder)

    opend_id = result_json['openid']
    session_key = result_json['session_key']

    param_dict = {
        "openid": opend_id,
        "session_key": session_key
    }
    wechatuser = wechat_service.wechat_register(param_dict)

    if wechatuser:
        result = {
            "meta": {
                "msg": "",
                "code": 0
            },
            "results": {
                "openid": opend_id,
                "session_key": session_key,
                "user_id":wechatuser.passport_user.id,
                "nickname":wechatuser.nickname,
                "avatar_url":wechatuser.avatar_url
            }
        }

        response = JsonResponse(result, encoder=DjangoJSONEncoder)
        # wechatuser.passport_user.last_login = datetime.now()
        return flush_cookie(wechatuser.passport_user, response)
        # return flush_wechat_cookie(session_key, response)
    else:
        result = {
            "meta": {
                "msg": "微信用户登录失败",
                "code": 20001
            },
            "results": {

            }
        }

        # return JsonResponse(result, encoder=DjangoJSONEncoder)
        response = JsonResponse(result, encoder=DjangoJSONEncoder)
        return flush_wechat_cookie("", response)

def flush_wechat_cookie(in_param,response):
    session_key = in_param
    response.set_cookie(key="sessionid", value=session_key, path="/", httponly=True, domain="*.hemaweidian.com",
                        max_age=7884000)
    return response

def flush_cookie(passport_user, response):
    try:
        session = Session.objects.get(passport_user_id=passport_user.id)
        # session.expire_date = datetime.now() + timedelta(seconds=int(settings.PASSPORT_MAX_AGE))
        session.save()
    except Session.DoesNotExist:
        session = Session(
            session_key=uuid.uuid4(),
            session_data=json.dumps({"id": passport_user.id}),
            expire_date=datetime.now() + timedelta(seconds=int(settings.PASSPORT_MAX_AGE)),
            passport_user=passport_user
        )
        session.save()
    response.set_cookie(key="hs_session", value=session.session_key, path="/", httponly=True, domain=settings.PASSPORT_COOKIE_DOMAIN,
                        max_age=int(settings.PASSPORT_MAX_AGE))
    return response
