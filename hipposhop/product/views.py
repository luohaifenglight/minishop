# -*- coding: utf-8 -*-
from django.http import JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from utils.serializer import DjangoJSONEncoder
# Create your views here.

@require_http_methods(["GET"])
@csrf_exempt
@cache_control(max_age=30)
def get_product_list(request):
    result = {
            "meta": {
                "code": 0,
                "msg": "success"
            },
            "results": {
                "gifts": [
                    {
                        "title": "免安装台式洗碗机",
                        "order_date": "2018-01-02",
                        "state": "已发货",
                        "express_name": "顺丰快递",
                        "pic_url": "http://",
                        "express_id": "运单号000000000000",
                        "count": 1
                    }
                ]
            }
        }
    return JsonResponse(result, encoder=DjangoJSONEncoder)