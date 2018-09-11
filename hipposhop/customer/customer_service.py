# -*- coding:utf-8 -*-
import logging
from order.orderservice import OrderService
from customer.models import JieLongUserRelation, JieLongSpreadUserRelation
from passport.models import WechatUser
from promotions.jielong_service import get_covert_user_nickname, covert_avatar_url

logger = logging.getLogger("django.request")


class CustomerService(object):

    @classmethod
    def paginator(cls):
        class Pagination(object):
            page_no = 1
            page_size = 20
            start = 0
            end = 20
        return Pagination()

    @classmethod
    def get_my_follows(cls, **kwargs):
        """ 我的关注 """
        pagination = kwargs.get("pagination", None)
        if not pagination:
            pagination = cls.paginator()

        follows = OrderService.order_queryset(**kwargs).values("seller_id").distinct()
        count = follows.count()
        follows = follows[pagination.start: pagination.end]
        if follows:
            follows = [f["seller_id"] for f in follows]
        logger.info("my_follows, kwargs: %s, count:%s, follows: %s" % (kwargs, count, follows))
        return follows, count

    @classmethod
    def get_my_fans_by_user_id(cls, user_id, pagination=None):
        """ 我的粉丝 """
        if not pagination:
            pagination = cls.paginator()

        fans = JieLongUserRelation.objects.filter(jielong__passport_user_id=user_id).values_list("passport_user_id", flat=True).distinct()
        count = fans.count()
        logger.info("my_fans, user_id: %s, count: %s" % (user_id, count))
        fans = fans[pagination.start: pagination.end]
        fans_list = []

        if fans:
            for f_id in fans:
                items_dict = {}
                we_user = WechatUser.objects.get(passport_user_id=f_id)
                items_dict["id"] = f_id
                items_dict["nick"] = get_covert_user_nickname(f_id, we_user.nickname)
                items_dict["avatar_url"] = covert_avatar_url(we_user.avatar_url)
                fans_list.append(items_dict)
        return fans_list, count

    @classmethod
    def get_my_spreaders_by_inviter_id(cls, inviter_id, pagination=None, is_all=False):
        if not pagination:
            pagination = cls.paginator()
        spreader_ids = JieLongSpreadUserRelation.objects.filter(status=1, invite_sponsor_id=inviter_id).values_list("passport_user_id", flat=True)
        count = spreader_ids.count()
        if not is_all:
            spreader_ids = spreader_ids[pagination.start: pagination.end]
        logger.info("get_spreaders,inviter_id: %s, is_all: %s, count: %s, spreader_ids: %s" % (inviter_id, is_all, count, spreader_ids))

        return spreader_ids, count

    @classmethod
    def get_spreaders_by_orderuser(cls, **kwargs):
        # query = OrderService._parse_query_params(**kwargs)
        logger.info("get_spreaders_by_orderuser, kwargs: %s")
        spread_user_ids = OrderService.order_queryset(**kwargs).values("spread_user_id").distinct()
        count = spread_user_ids.count()
        if count > 0:
            spread_user_ids = [s["spread_user_id"] for s in spread_user_ids]
        return spread_user_ids, count

