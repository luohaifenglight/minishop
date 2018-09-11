# -*- coding: utf-8 -*-
import json
import os
import hashlib

from django.http import JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from utils.serializer import DjangoJSONEncoder
from django.core.files.storage import default_storage

from utils.serializer import DjangoJSONEncoder


# Create your views here.


def get_image_path(instance, filename, imgfield):
    base = "hsupload/"
    parts = os.path.splitext(filename)
    ctx = hashlib.sha256()
    if imgfield.multiple_chunks():
        for data in imgfield.chunks(imgfield.DEFAULT_CHUNK_SIZE):
            ctx.update(data)
    else:
        ctx.update(imgfield.read())
    return os.path.join(base, ctx.hexdigest() + parts[1])


@csrf_exempt
def upload(request):
    image = request.FILES.get('file', None)
    save_path = get_image_path(None, image.name, image)
    path = default_storage.save(save_path, image)
    from .fileservice import get_full_path
    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "path": get_full_path(path),
            "uri": path
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)


@require_http_methods(["POST"])
@csrf_exempt
def share(request, **kwargs):
    # userid = kwargs.get("userid", 1)
    order_dict = json.loads(request.body)
    jielong_id = order_dict.get("jielong_id", None)
    user_id = order_dict.get("user_id", None)
    from .combineimage import CombineImage
    # path = CombineImage.share_image(jielong_id, userid)
    qrcode_url = CombineImage.share_qrcode_url(jielong_id,user_id)
    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "path": qrcode_url,
        }
    }
    return JsonResponse(result, encoder=DjangoJSONEncoder)
