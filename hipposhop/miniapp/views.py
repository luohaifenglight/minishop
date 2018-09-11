# -*- coding: utf-8 -*-
import collections
import hashlib
import json
import logging
from urllib.parse import urlencode

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from miniapp.models import QRCodeURLParam, save_qr_code, get_qr_code_obj
from miniapp.wechat_service import get_access_token, get_qr_code_image, get_token_cache_key
from utils.oss_file import OssFileUtil
from utils.redis_common_util import RedisCommonUtil
from utils.serializer import DjangoJSONEncoder

logger = logging.getLogger("django.request")


def _query_string_of(query_param):
    d1 = collections.OrderedDict(sorted(query_param.items(), key=lambda t: t[0]))
    return urlencode(d1)


@require_http_methods(["POST"])
@csrf_exempt
def get_qr_code(request, **kwargs):
    param_dict = json.loads(request.body)
    page = param_dict.get("page")
    query_param = param_dict.get("param")
    logger.info("get_qr_code page:%s;param:%s" % (page, query_param))
    error_message = ''
    access_token = None
    if not query_param or not page:
        error_message = '缺少参数'
    if len(error_message) < 1:
        access_token = get_access_token()
        if not access_token:
            error_message = 'token获取失败'
    if len(error_message) > 0:
        result = {
            "meta": {
                "msg": error_message,
                "code": 2
            },
            "results": {
            }
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    qr_code_url = None
    try:
        query_string = _query_string_of(query_param)
        db_key = "%s:%s" % (page, query_string)
        md5_key = hashlib.md5(db_key.encode('utf-8')).hexdigest()
        items = QRCodeURLParam.objects.filter(md5_key=md5_key)
        if len(items) > 0:
            qr_code_url = items.first().qr_code_url
        if not qr_code_url or len(qr_code_url) < 1:
            qr_obj = save_qr_code(page, query_string, md5_key)
            if not qr_obj:
                raise Exception("二维码缓存数据失败")
            resp = get_qr_code_image(access_token, qr_obj.id, page)
            if resp.status_code == 200:
                if 'application/json' in resp.headers["Content-Type"].lower():
                    json1 = resp.json()
                    if json1["errcode"] == 40001:
                        key = get_token_cache_key()
                        RedisCommonUtil.del_data(key)
                    raise Exception("二维码缓存数据失败%s" % resp.text)
                else:
                    oss = OssFileUtil()
                    oss.item_pic_base = "miniapp"
                    qr_code_url = oss.upload_bytes(resp.content, md5_key)
                    if qr_code_url:
                        qr_obj.qr_code_url = qr_code_url
                        qr_obj.save()
                    else:
                        raise Exception("二维码图片保存失败")
        if not qr_code_url or len(qr_code_url) < 1:
            raise Exception("二维码图片生成失败")

    except Exception as e:
        error_message = "%s" % e
        print(e)
        result = {
            "meta": {
                "msg": error_message,
                "code": 12
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
            "qr_code_url": qr_code_url
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["GET"])
@csrf_exempt
def get_qr_param(request, **kwargs):
    qr_id = request.GET.get("id", None)
    error_message = ''
    if not qr_id:
        error_message = '参数错误'
    obj = None
    if len(error_message) < 1:
        obj = get_qr_code_obj(qr_id)
        if not obj:
            error_message = "没有相关数据"
    if obj:
        result = {
            "meta": {
                "msg": "",
                "code": 0
            },
            "results": {
                "query_param": obj.query_param
            }
        }
    else:
        result = {
            "meta": {
                "msg": error_message,
                "code": 1
            },
            "results": {}
        }
    logger.info("get_qr_param result:%s" % (result))
    return JsonResponse(result, encoder=DjangoJSONEncoder)
