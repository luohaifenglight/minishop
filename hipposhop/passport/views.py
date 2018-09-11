# -*- coding: utf-8 -*-
import json
import logging

from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from passport import wechat_service
from passport.decorators import wechat_user_auth
from passport.models import WechatUser, PassportUser
from utils.serializer import DjangoJSONEncoder

logger = logging.getLogger('django.request')
# Create your views here.

@require_http_methods(["GET"])
@csrf_exempt
@never_cache
def register(request):
    return True


@require_http_methods(["GET"])
@csrf_exempt
@never_cache
def login(request):
    return True


@require_http_methods(["POST"])
@csrf_exempt
def test(request, **kwargs):
    param_dict = json.loads(request.body)
    passport_user = PassportUser()
    passport_user.user_name = param_dict.get("p_name")
    passport_user.password = param_dict.get("p_word")
    passport_user.mobile = param_dict.get("p_mobile")
    passport_user.save()

    wechat = WechatUser()
    wechat.nickname = param_dict.get("wx_name")
    wechat.password = param_dict.get("wx_image")
    wechat.unionid = param_dict.get("wx_unionid")
    wechat.passport_user_id = passport_user.id
    wechat.save()

    result = {
        "meta": {
            "msg": "",
            "code": 0
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@wechat_user_auth
@csrf_exempt
def update_user_info(request, **kwargs):
    user_id = kwargs.get("userid")
    user = WechatUser.objects.get(passport_user_id = user_id)
    param_dict = json.loads(request.body)

    try:
        # session_key = param_dict.get("session_key")
        # openid = param_dict.get("openid")
        session_key = user.session_key
        openid = user.openid
        iv = param_dict.get("iv")
        encrypted_data = param_dict.get("encrypted_data")
        user_json = wechat_service.get_user_info(session_key, encrypted_data, iv)
        unionid = ""
        if "unionId" in user_json:
            unionid = user_json["unionId"]
        param_dict = {
            "openid": openid,
            "session_key": session_key,
            "nickname": user_json["nickName"],
            "avatar_url": user_json["avatarUrl"],
            "unionid": unionid,
        }
        logger.info("update_user_info  param_dict %s" % (param_dict))
        wechatuser = wechat_service.wechat_register(param_dict)
    except Exception as e:
        error_message = '微信用户信息更新失败'
        print(e)
        result = {
            "meta": {
                "msg": error_message,
                "code": 20002
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
            "nickname": wechatuser.nickname,
            "avatar_url": wechatuser.avatar_url,
        }
    }

    return JsonResponse(result, encoder=DjangoJSONEncoder)

@require_http_methods(["POST"])
@wechat_user_auth
@csrf_exempt
def update_user_detail_info(request, **kwargs):
    user_id = kwargs.get("userid")
    param_dict = json.loads(request.body)

    try:
        nickname = param_dict.get("nickname",None)
        avatar_url = param_dict.get("avatar_url",None)

        param_dict = {}
        if nickname:
            param_dict["nickname"] = nickname
        if avatar_url:
            param_dict["avatar_url"] = avatar_url
        logger.warning("update_user_detail_info: %s" % param_dict)

        if "nickname" in param_dict or "avatar_url" in param_dict:
            wechatuser = WechatUser.objects.update_or_create(passport_user_id=user_id,defaults=param_dict)
            result = {
                "meta": {
                    "msg": "",
                    "code": 0
                },
                "results": {
                    "nickname": nickname,
                    "avatar_url": avatar_url,
                }
            }
        else:
            result = {
                "meta": {
                    "msg": "用户请求参数信息不完整",
                    "code": 13
                },
                "results": {
                }
            }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

    except Exception as e:
        error_message = '微信用户信息更新失败'
        result = {
            "meta": {
                "msg": error_message,
                "code": 20002
            },
            "results": {
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)

