import logging
from datetime import datetime
from functools import wraps

from django.contrib import auth
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import (
    available_attrs,
)

from passport.models import WechatUser, Session

logger = logging.getLogger('django.request')


class HttpResponseUnauthorized(HttpResponse):
    status_code = 401

def wechat_user_auth(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view_func(request, *args, **kwargs):
        session_key = request.COOKIES.get("hs_session", None)
        logger.debug("cookie %s" % (session_key,))
        if session_key is None:
            return HttpResponseUnauthorized("session is none")
        try:
            # wechat = WechatUser.objects.get(session_key=session_key)
            # kwargs["userid"] = wechat.passport_user_id
            # logger.info("cookie %s %s" % (session_key, wechat.passport_user_id))
            s = Session.objects.get(session_key=session_key)
            kwargs["userid"] = s.passport_user_id
            logger.info("cookie %s %s" % (session_key, s.passport_user_id))
            current_date = datetime.now()
            # s.passport_user.last_login = current_date
            s.passport_user.save()
        except WechatUser.DoesNotExist as e:
            print(e)
            logger.warning("session not found, return 401, %s" % request)
            return JsonResponse(data={"status": 1, "err": "session not found"}, status=401)

        return view_func(request, *args, **kwargs)

    return _wrapped_view_func


def admin_auth(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view_func(request, *args, **kwargs):
        user = auth.get_user(request)
        if user.id is None:
            logger.warning("session not found, return 401, %s" % request)
            return JsonResponse(data={"status": 1, "err": "session not found"}, status=401)
        return view_func(request, *args, **kwargs)

    return _wrapped_view_func
