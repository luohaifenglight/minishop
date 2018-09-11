#! coding:utf-8

import random
import hashlib
import json
import base64
import time
import datetime
from urllib.request import quote
import requests
import xml.etree.ElementTree as ET




def utc2local(utc_st):
    """UTC时间转本地时间（+8:00"""
    now_stamp = time.time()
    local_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = utc_st + offset
    local_st = local_st.replace(tzinfo=None)
    return local_st


def local2utc(local_st):
    """本地时间转UTC时间（-8:00）"""
    time_struct = time.mktime(local_st.timetuple())
    utc_st = datetime.datetime.utcfromtimestamp(time_struct)
    utc_st = utc_st.replace(tzinfo=datetime.timezone.utc)
    return utc_st

class WechartPay(object):
    def __init__(self):
        self.appid = ""
        self.mch_id = ""
        self.nonce_str = ""
        self.sign = ""
        self.body = u"团购商品费用".encode("utf-8")
        self.out_trade_no = "12314"
        self.total_fee = 1024
        self.spbill_create_ip = "124.204.36.26"
        #self.spbill_create_ip = "120.78.149.217"
        self.notify_url = ""
        self.trade_type = "JSAPI"
        self.openid = ""
        # 商户支付密钥Key。审核通过后，在微信发送的邮件中查看
        self.key = ""

    def get_nonce_str(self, length=32):
        # get random str
        """产生随机字符串，不长于32位"""
        chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        strs = []
        for x in range(length):
            strs.append(chars[random.randrange(0, len(chars))])
        return "".join(strs)

    def formatBizQueryParaMap(self, paraMap, urlencode):
        """格式化参数，签名过程需要使用"""
        slist = sorted(paraMap)
        buff = []
        for k in slist:
            v = quote(paraMap[k]) if urlencode else paraMap[k]
            buff.append("{0}={1}".format(k, v))

        return "&".join(buff)

    def _get_sign(self, obj):
        # get sign
        """生成签名"""
        # 签名步骤一：按字典序排序参数,formatBizQueryParaMap已做
        String = self.formatBizQueryParaMap(obj, False)
        # 签名步骤二：在string后加入KEY
        String = "{0}&key={1}".format(String, self.key)
        # 签名步骤三：MD5加密
        String = hashlib.md5(String.encode("utf-8")).hexdigest()
        # 签名步骤四：所有字符转为大写
        result_ = String.upper()
        return result_

    def _get_obj(self):
        obj = {
            "appid": self.appid,
            "mch_id": self.mch_id,
            "body": self.body,
            "out_trade_no": self.out_trade_no,
            "total_fee": self.total_fee,
            "spbill_create_ip": self.spbill_create_ip,
            "notify_url": self.notify_url,
            "trade_type": self.trade_type,
            "nonce_str": self.nonce_str,
            "openid": self.openid,
        }
        return obj

    def product_sign(self, obj):
        return self._get_sign(obj)

    def to_xml(self, open_id):
        self.openid = open_id
        self.nonce_str = self.get_nonce_str()
        obj = self._get_obj()
        sign = self._get_sign(obj)
        obj["sign"] = sign
        return self._array_to_xml(obj)

    def _array_to_xml(self, arr):
        """array转xml"""
        xml = ["<xml>"]
        for k, v in arr.items():
            if str(v).isdigit():
                xml.append("<{0}>{1}</{0}>".format(k, v))
            else:
                xml.append("<{0}><![CDATA[{1}]]></{0}>".format(k, v))
        xml.append("</xml>")
        return "".join(xml).encode("utf-8")

    def get_order_info(self, out_trade_no):
        """
        主动查询微信支付结果订单
        :param out_trade_no: 
        :return: 
        """
        obj = {
            "appid": self.appid,
            "mch_id": self.mch_id,
            "out_trade_no": out_trade_no,
            "nonce_str": self.get_nonce_str(),
        }
        sigin = self.product_sign(obj)
        obj["sign"] = sigin
        xml = self._array_to_xml(obj)
        query_url = "https://api.mch.weixin.qq.com/pay/orderquery"
        result = requests.post(query_url, data=xml).text
        result_dict = WechartPay.xml_to_dict(result)
        return result_dict

    @classmethod
    def xml_to_dict(cls, xml):
        """将xml转为array"""
        return dict((child.tag, child.text) for child in ET.fromstring(xml))


class WechartWithdrawCash(WechartPay):
    withdrawcash_url = "https://api.mch.weixin.qq.com/mmpaymkttransfers/promotion/transfers"
    cert = ('config/cert/0815do9xci_c.pem', 'config/cert/0815do9xci_k.pem')

    def _get_obj(self):
        obj = {
            "mch_appid": self.appid,
            "mchid": self.mch_id,
            # "body": self.body,
            "partner_trade_no": self.out_trade_no,
            "amount": self.total_fee,
            "spbill_create_ip": self.spbill_create_ip,
            # "notify_url": self.notify_url,
            # "trade_type": self.trade_type,
            "nonce_str": self.nonce_str,
            "openid": self.openid,
            "check_name": "FORCE_CHECK",
            "re_user_name": self.re_user_name,
            "desc": "河马提现"

        }
        return obj

    def withdraw_cash(self, open_id, money, real_name=""):
        from decimal import Decimal
        self.total_fee = int(Decimal(money) * 100)
        self.re_user_name = real_name
        # need set order_num, price, and next
        params = self.to_xml(open_id)
        data = requests.post(self.withdrawcash_url, data=params, cert=self.cert)
        result_json = WechartPay.xml_to_dict(data.text)
        return result_json

    def check_withdraw_cash_err_des(cls, err_desc):
        try:
            if "余额不足" in err_desc:
                return "提现失败，稍后重试或联系客服"
            else:
                return err_desc
        except Exception as e:
            return err_desc


class WechatRefund(WechartPay):
    withdrawcash_url = "https://api.mch.weixin.qq.com/secapi/pay/refund"
    key = "xxxxxx"
    cert = ('config/cert/0815do9xci_c.pem', 'config/cert/0815do9xci_k.pem')

    def _get_obj(self):
        obj = {
            "appid": self.appid,
            "mch_id": self.mch_id,
            # "body": self.body,
            "out_trade_no": self.out_trade_no,
            "out_refund_no": self.out_refund_no,
            "total_fee": self.total_fee,
            "refund_fee": self.refund_fee,
            "notify_url": self.notify_url,
            # "trade_type": self.trade_type,
            "nonce_str": self.nonce_str,
        }
        if self.refund_desc:
            obj["refund_desc"] = self.refund_desc
        return obj

    def apply_refund(self, out_trade_no, out_refund_no, money, refund_desc=""):
        self.out_trade_no = out_trade_no
        self.out_refund_no = out_refund_no
        from decimal import Decimal
        self.total_fee = int(Decimal(money) * 100)
        self.refund_fee = int(Decimal(money) * 100)
        self.refund_desc = refund_desc
        self.notify_url = ""
        # need set order_num, price, and next
        params = self.to_xml("")
        print(params)
        data = requests.post(self.withdrawcash_url, data=params, cert=self.cert)
        print(data.text)
        result_json = WechartPay.xml_to_dict(data.text)
        return result_json

    @classmethod
    def _get_key(cls):
        mymd5 = hashlib.md5()
        mymd5.update(cls.key.encode("utf-8"))
        result = mymd5.hexdigest()
        return result

    @classmethod
    def decrypt(cls, req_info):
        from .decrypt import AESCommon
        key = cls._get_key()
        req_info = base64.b64decode(req_info)
        result = AESCommon.decrypt(req_info, key)
        result = cls.xml_to_dict(result)
        print(result)
        return result







if __name__ == '__main__':
    wp = WechartPay()
    params = wp.to_xml("oG8AM5De1WqO35H4K60NpNbIAJ-Q")
    url = "https://api.mch.weixin.qq.com/pay/unifiedorder"
    data = requests.post(url, data=params)
    print ("appid", wp.appid)
    print ("mch_id", wp.mch_id)
    print (data.text)
    result_json = WechartPay.xml_to_dict(data.text)
    print (result_json)
    print (data.status_code)


