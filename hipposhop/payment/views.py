# -*- coding: utf-8 -*-
import json

from django.http import JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from passport.decorators import wechat_user_auth
from passport.models import PassportUser

from utils.serializer import DjangoJSONEncoder
from order.orderservice import OrderService
from customer.models import JieLong
from .wechartpay import WechartPay, local2utc, WechatRefund
from .payservice import PayService
from .refundservice import ReFundService
import time
import requests
import logging
logger = logging.getLogger("django")


# Create your views here.

@require_http_methods(["POST"])
@wechat_user_auth
@csrf_exempt
def order_pay(request, **kwargs):
    pay_dict = json.loads(request.body)
    open_id = pay_dict.get('openid')
    user_id = kwargs.get("userid", 1)
    user = PassportUser.objects.get(id=user_id)
    open_id = user.wechatuser.openid or open_id
    order_id = pay_dict.get("order_id")
    if not PayService.check_pay(order_id):
        result = {
            "meta": {
                "msg": "订单已支付",
                "code": 1
            },
            "results": {}
        }
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    price = pay_dict.get("price")
    adress = pay_dict.get("address")
    address = {}
    convert_keys = [
      'telNumber',
      'postalCode',
      'userName',
      'provinceName',
      'countyName',
      'cityName',
      'detailInfo',
      'nationalCode',

    ]
    adress_keys = [
            "mobile",
            "postal_code",
            "name",
            "province",
            "country",
            "city",
            "address_detail",
            "national_code"
        ]
    for index, add in enumerate(adress):
        address[adress_keys[index]] = adress.get(convert_keys[index], "")
    test_atttr = {
        "openid": "",
        "order_id": "",
        "price": "",
        "address": {
            "mobile": "",
            "postal_code": "",
            "name": "",
            "province": "",
            "country": "",
            "city": "",
            "address_detail":"",
            "national_code": "",
        },
    }
    wp = WechartPay()
    out_trade_no = str(int(time.time() * 1000))
    wp.out_trade_no = out_trade_no
    wp.body = order_id
    from decimal import Decimal
    orders_ = OrderService.order_detail(order_id)
    wp.total_fee = int(orders_.get("order_price") * 100)
    # need set order_num, price, and next
    params = wp.to_xml(open_id)
    url = "https://api.mch.weixin.qq.com/pay/unifiedorder"
    data = requests.post(url, data=params)
    result_json = WechartPay.xml_to_dict(data.text)
    logger.info(result_json)
    data_list = {}
    if result_json.get("result_code", "") == "SUCCESS":
        data_list = {
            "appId": result_json.get("appid"),
            "timeStamp": str(int(time.time())),
            "nonceStr": wp.get_nonce_str(),
            "package": "prepay_id=%s" % result_json.get("prepay_id"),
            "signType": "MD5"

        }
        pay_sign = wp.product_sign(data_list)
        data_list["paySign"] = pay_sign
        PayService.order_logic(user_id, result_json, price, open_id, order_id, address, out_trade_no)
        result = {
            "meta": {
                "msg": "",
                "code": 0
            },
            "results": data_list
        }
    else:
        result = {
            "meta": {
                "msg": result_json.get("err_code_des", ""),
                "code": 1
            },
            "results": {}
        }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@csrf_exempt
def get_order(request):
    orders = request.body
    result_json = WechartPay.xml_to_dict(orders)
    logger.info(result_json)
    wp = WechartPay()
    sign = result_json.pop("sign")
    my_sign = wp.product_sign(result_json)
    if sign != my_sign:
        return HttpResponse('''
            <xml>

          <return_code><![CDATA[FAIL]]></return_code>
          <return_msg><![CDATA[cao ni ma!]]></return_msg>
        </xml>
            ''', content_type="text/xml")
    logger.info("auync---")
    xml = '''<xml>

  <return_code><![CDATA[SUCCESS]]></return_code>
  <return_msg><![CDATA[OK]]></return_msg>
</xml>'''
    if result_json.get("return_code") == "SUCCESS":
        PayService.save_pay_order(result_json)
        return HttpResponse(xml, content_type="text/xml")
    return HttpResponse('''
    <xml>

  <return_code><![CDATA[FAIL]]></return_code>
  <return_msg><![CDATA[NOT OK]]></return_msg>
</xml>
    ''', content_type="text/xml")


@csrf_exempt
def get_refund_order(request):
    orders = request.body
    result_json = WechartPay.xml_to_dict(orders)
    logger.info(result_json)
    logger.info("auync---")
    xml = '''<xml>

  <return_code><![CDATA[SUCCESS]]></return_code>
  <return_msg><![CDATA[OK]]></return_msg>
</xml>'''
    if result_json.get("return_code") == "SUCCESS":
        ReFundService.sync_refund_order(result_json)

        return HttpResponse(xml, content_type="text/xml")
    return HttpResponse('''
    <xml>

  <return_code><![CDATA[FAIL]]></return_code>
  <return_msg><![CDATA[NOT OK]]></return_msg>
</xml>
    ''', content_type="text/xml")


@csrf_exempt
def test_hack(request):
    orders = request.body
    from io import StringIO
    from lxml import etree
    magical_parser = etree.XMLParser(encoding='utf-8')

    result_json = etree.parse(StringIO(orders), magical_parser)
    logger.info(result_json)
    logger.info("auync---")
    xml = '''<xml>

  <return_code><![CDATA[SUCCESS]]></return_code>
  <return_msg><![CDATA[OK]]></return_msg>
</xml>'''
    if result_json.get("return_code") == "SUCCESS":
        # PayService.save_pay_order(result_json)
        ReFundService.sync_refund_order(result_json)
        return HttpResponse(xml, content_type="text/xml")
    return HttpResponse('''
    <xml>

  <return_code><![CDATA[FAIL]]></return_code>
  <return_msg><![CDATA[NOT OK]]></return_msg>
</xml>
    ''', content_type="text/xml")
