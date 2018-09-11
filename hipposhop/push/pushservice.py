#! coding: utf-8

import logging
import requests

from urllib.parse import urlencode


logger = logging.getLogger("django")


class PushBaseMessage(object):
    template_id = "O1PZqXfYTMqXMcgrFdSuY0WUxYbsnMhbRx_s_PYmUpE" # 覆盖你的模版ID
    template_api = "https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send"

    @classmethod
    def _get_access_token(cls):
        from miniapp.wechat_service import get_access_token
        access_token = get_access_token()
        logger.info("access_token%s", access_token)
        return access_token

    @classmethod
    def _get_url(cls):
        params = {
            'access_token': cls._get_access_token()
        }
        data = urlencode(params)
        url = "%s?%s" % (cls.template_api, data)
        return url

    @classmethod
    def format_data(cls, data):
        raise NotImplementedError("需要格式化")

    @classmethod
    def send_message(cls, open_id, prepay_id, data):
        request_json = {
            "touser": open_id,
            "template_id": cls.template_id,
            "page": "",
            "form_id": prepay_id,
            "data": cls.format_data(data),
            "emphasis_keyword": ""
        }
        headers = {'content-type': 'application/json'}
        result = requests.post(cls._get_url(), json=request_json, headers=headers)
        logger.info(result.json())
        return result.json()
