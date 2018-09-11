# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
from urllib.parse import urlencode

import requests

# app 用
from django.conf import settings
from passport.models import PassportUser, WechatUser
from utils.WXBizDataCrypt import WXBizDataCrypt

logger = logging.getLogger("django.request")


def get_user_info(session_key, encrypted_data, iv):
    """
    参数由前端获取，小程序wx.login后走用户授权，之后调用wx.getUserInfo接口获取相关参数
    :param session_key:
    :param encrypted_data:
    :param iv:
    :return:
    """
    pc = WXBizDataCrypt(settings.MINI_APPID, session_key)
    return pc.decrypt(encrypted_data, iv)


def wechat_jscode2session(code, app_id=settings.MINI_APPID, secret=settings.MINI_SECRET):
    code = code
    params = {
        'appid': app_id,
        'secret': secret,
        'js_code': code,
        'grant_type': 'authorization_code'
    }
    data = urlencode(params)
    first = 'https://api.weixin.qq.com/sns/jscode2session?%s'
    result_url = first % data
    open_data = requests.get(result_url)
    result_data = json.loads(open_data.text)
    return result_data


def get_wechat_error_info(result_json):
    if 'errcode' in result_json:
        try:
            error_message = '%s(%s)' % (result_json['errmsg'], result_json['errcode'])
        except Exception as e:
            error_message = '微信授权失败(数据解析异常)'
            print(e)
        return {
            "meta": {
                "msg": error_message,
                "code": 1002
            },
            "results": {}
        }

    return None


def update_wechat_user(param_dict, wechat_user):
    try:
        if "unionid" not in param_dict:
            return wechat_user
        wechat_user.unionid = param_dict["unionid"]
        wechat_user.nickname = param_dict["nickname"]
        wechat_user.avatar_url = param_dict["avatar_url"]
        wechat_user.save()
        return wechat_user
    except Exception as e:
        print(e)
        return None


def wechat_register(param_dict):
    openid = param_dict.get("openid")
    session_key = param_dict.get("session_key")
    try:
        wechatuser = WechatUser.objects.get(openid=openid)
        # if len(items) > 0:
        #     return update_wechat_user(param_dict, items.first())


        if "unionid" in param_dict:
            w_dict = {
                "unionid": param_dict["unionid"],
                "nickname": param_dict["nickname"],
                "avatar_url": param_dict["avatar_url"],
                "session_key":param_dict["session_key"]
            }
            logger.info("wechat_register unionid not none: w_dict %s" % (w_dict))
            wechatuser,status = WechatUser.objects.update_or_create(openid=openid,defaults=w_dict)
            return wechatuser
        else:
            w_dict = {
                "session_key":param_dict["session_key"],
                "openid": param_dict["openid"]
            }
            if "nickname" in param_dict:
                w_dict["nickname"] = param_dict["nickname"]
            if "avatar_url" in param_dict:
                w_dict["avatar_url"] = param_dict["avatar_url"]


            logger.info("wechat_register unionid none: w_dict %s" % (w_dict))
            wechatuser,status = WechatUser.objects.update_or_create(openid=openid,defaults=w_dict)
            return wechatuser
    except WechatUser.DoesNotExist:
        try:
            passport_user = PassportUser()
            passport_user.is_active = True
            passport_user.save()

            wechatuser = WechatUser()
            wechatuser.openid = openid
            wechatuser.session_key = session_key
            wechatuser.passport_user_id = passport_user.id
            if "unionid" in param_dict:
                wechatuser.unionid = param_dict["unionid"]
            if "nickname" in param_dict:
                wechatuser.nickname = param_dict["nickname"]
            if "avatar_url" in param_dict:
                wechatuser.avatar_url = param_dict["avatar_url"]
            if "openid" in param_dict:
                wechatuser.openid = param_dict["openid"]
            if "session_key" in param_dict:
                wechatuser.session_key = param_dict["session_key"]

            logger.info("wechat_register don't exist param_dict %s" % (param_dict))

            wechatuser.save()
            return wechatuser
        except Exception as e:
            print(e)
            return None
