# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from functools import reduce

from django.db.models import Sum, Count

from customer.models import ShareUserRelation, JieLongSpreadUserRelation, JieLongUserRelation
from order.orderservice import OrderService
from product.models import Product
from promotions.models import JieLong, JielongProductRelation
from utils.date_util import UtilDateTime

logger = logging.getLogger('django.request')

def get_jielong_detail(activity_id,user_id):
    try:
        jielong = JieLong.objects.get(id=activity_id)
        create_time = "%s发起" % get_time_span(UtilDateTime.utc2local(jielong.create_time))
        end_time = "截止时间：%s" % (UtilDateTime.utc2local(jielong.end_time))
        opt_start = UtilDateTime.utc2local2m(jielong.create_time)
        opt_end = UtilDateTime.utc2local2m(jielong.end_time)
        opt_time = "活动时间：%s 至 %s" % (opt_start,opt_end)
        browse_num = "%s人看过" % (jielong.browse_num)
        title = jielong.title
        desc = jielong.description
        sm = [sm for sm in jielong.small_images.split(" ")]

        products = JielongProductRelation.objects.filter(jielong_id=activity_id,is_valid=0)
        product = []
        share_browse_num = get_browse_nums_by_spreaduser(activity_id,user_id)
        if products:
            for p in products:
                if p.product.small_images:
                    p_sm = [p_sm for p_sm in p.product.small_images.split(" ")]
                    small_image = p.product.small_images.split(" ")[0]
                else:
                    small_image = "https://i1.hemaweidian.com/hsupload/67c7319bfa9323111576a20ee2a4b2f6f1f3dd98d1efa63ee62088ae85be0d08.jpg"
                    p_sm = ["https://i1.hemaweidian.com/hsupload/67c7319bfa9323111576a20ee2a4b2f6f1f3dd98d1efa63ee62088ae85be0d08.jpg"]
                item = {
                    "goods_id":p.product.id,
                    "pic_url": small_image,
                    "pics_url": p_sm,
                    "title": p.product.title,
                    "specifications_info": p.product.sku_desc,
                    "detail_info":p.product.description,
                    "order_info": "已团%s" % (p.product.volume),
                    "price": p.product.zk_final_price,
                    "sku_num": p.product.sku_num,
                    "sku_default_num": "0"
                }
                product.append(item)

    except JieLong.DoesNotExist:
        result = {
            "meta": {
                "msg": "活动不存在",
                "code": 30001
            },
            "results": {}
        }
        return result
    spread_user = JieLongSpreadUserRelation.objects.filter(passport_user_id=user_id,invite_sponsor_id=jielong.passport_user_id,status=1)
    if spread_user:
        share_content = "分享团购产生成交，您就能获得交易额%s%s的奖励" % (jielong.commission_rate,"%")
    else:
        share_content = ""
    order_list,count = OrderService.order_list(spread_user_id=user_id,jielong_id=activity_id)
    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "seller_id":jielong.passport_user.id,
            "avatar_url":covert_avatar_url(jielong.passport_user.wechatuser.avatar_url),
            "nickname":get_covert_user_nickname(jielong.passport_user.id,jielong.passport_user.wechatuser.nickname),
            # "share_image":"http://image.hemazou.com/adminupload/bad9109096bdb7e6cb729cc91d66f7e8e8c141d8d24af7c52054e300e8d45bf6.jpg",
            "share_content":share_content,
            "openid":jielong.passport_user.wechatuser.openid,
            "status":get_jielong_status(jielong.id),
            "create_time": create_time,
            "end_time": end_time,
            "opt_time":opt_time,
            "view_history": browse_num,
            "title": title,
            "detail_info": desc,
            "pic_url": sm,
            "goods": product,
            "invite_info": {
                "title": "我已邀请%s人浏览 , %s人下单" % (share_browse_num,count)
            }
        }
    }
    return result

def get_product_list_by_jielong(jielong_id):
    jielong_prods = JielongProductRelation.objects.filter(jielong_id=jielong_id,is_valid=0)
    products = []
    for jp in jielong_prods:
        item = {
            "id":jp.product_id,
            "title":jp.product.title,
            "info":jp.product.description,
            "images":[sm for sm in jp.product.small_images.split(" ")] if jp.product.small_images else [],
            "price":jp.product.zk_final_price,
            "count":jp.product.sku_num,
            "specifications":jp.product.sku_desc
        }
        products.append(item)
    return products

def update_jielong_by_id(jielong_id,param_dict):
    jielong_id = param_dict.get("operation").get("id")
    title = param_dict.get("operation").get("title")
    description = param_dict.get("operation").get("info")
    images = param_dict.get("operation").get("images")
    small_image = " ".join(images)
    begin_time = UtilDateTime.timestr_to_datetime(param_dict.get("others").get("start_time"))
    end_time = UtilDateTime.timestr_to_datetime(param_dict.get("others").get("end_time"))
    small_images = small_image
    commission_rate = param_dict.get("others").get("commission")
    wechat_no = param_dict.get("others").get("wechat_id")
    is_logistics = param_dict.get("others").get("logistics")

    jielong_dict = {
        "title": title,
        "description": description,
        "small_images": small_images,
        "begin_time": begin_time,
        "end_time": end_time,
        "commission_rate": commission_rate,
        "wechat_no": wechat_no,
        "is_logistics": is_logistics
    }
    jielong = JieLong.objects.update_or_create(id=jielong_id,defaults=jielong_dict)
    return True

def update_product_by_id(jielong_id,product_id,param_dict):
    product = Product.objects.update_or_create(id=product_id,defaults=param_dict)
    return True

def get_time_span(local_time):
    current_time = datetime.now()
    local_time = UtilDateTime.timestr_to_datetime(local_time)
    days = (current_time - local_time).days
    seconds = ((current_time - local_time).seconds)
    if days > 0:
        time_tip = "%s天前" % days
    elif seconds <300:
        time_tip = "刚刚"
    elif seconds < 3600:
        second = seconds / 60
        time_tip = "%s分钟前" % int(second)
    else:
        hour = seconds / 3600
        time_tip = "%s小时前" % int(hour)
    return time_tip

def get_browse_nums_by_spreaduser(activity_id,user_id):
    share_browse_num = ShareUserRelation.objects.filter(jielong_id=activity_id,share_user_id=user_id).aggregate(browse_num__sum=
                Count('browse_user'))["browse_num__sum"]

    logger.info("get_browse_nums_by_spreaduser activity_id: %s;user_id:%s;browse_num:%s" % (activity_id,user_id,share_browse_num))
    if share_browse_num:
        return share_browse_num
    else:
        return 0


def edit_jielong_product(dict,jielong_id):
    jp = JielongProductRelation.objects.filter(jielong_id=jielong_id,is_valid=0)
    if jp:
        for j in jp:
            j.is_valid = 1
            j.save()
            logger.info("edit_jielong_product activity_id: %s;product_id: %s" % (jielong_id,j.product.id))
    else:
        logger.info("edit_jielong_product activity_id: %s" % (jielong_id))

    goods = dict.get("goods")
    for i in goods:
        if "id" in i:
            goods_id = i["id"]
        else:
            goods_id = None
        images = i["images"]
        small_image = " ".join(images)
        title = i["title"]
        description = i["info"]
        sku_desc = i["specifications"]
        zk_final_price = i["price"]
        sku_num = i["count"]

        if not goods_id:
            prod = Product()
            prod.title =  title
            prod.description = description
            prod.sku_desc = sku_desc
            prod.zk_final_price = zk_final_price
            prod.sku_num = sku_num
            prod.max_buy_limit = 100
            prod.small_images = small_image
            prod.volume = 0
            prod.save()
            goods_id = prod.id
            # logger.info("edit_jielong_product add-product-info %s;goods_id:%s" % (prod, goods_id))
        else:
            prod_dict = {
                "title": title,
                "description": description,
                "sku_desc": sku_desc,
                "zk_final_price": zk_final_price,
                "sku_num": sku_num,
                "small_images":small_image
            }
            Product.objects.update_or_create(id=goods_id, defaults=prod_dict)
        jp_dict = {
            "is_valid":0
        }
        jielong_prod = JielongProductRelation.objects.update_or_create(product_id=goods_id,jielong_id=jielong_id,defaults=jp_dict)
        logger.info("edit_jielong_product param-info %s;jielong_id:%s" % (dict, jielong_id))

    return True

def format_index_jielong_order(order_param):
    order_list = []
    if len(order_param) > 0:
        sort = len(order_param)
        for o in order_param:
            item = {
                "time_info":get_time_span(o["order_time"].strftime("%Y-%m-%d %H:%M:%S")),
                "order":sort,
                "avatar_url":covert_avatar_url(o["avatar_url"]),
                "avatar_owner":get_covert_user_nickname(o["user_id"],o["nickname"]),
                "goods":o["goods"]
            }
            order_list.append(item)
            sort -= 1
    return order_list


def get_jielong_list_by_spread_user(user_id,start,end):
    '''
    根据发起人id获取接龙列表
    :param user_id:
    :return:
    '''
    jielongs = JieLong.objects.filter(passport_user_id=user_id).order_by("-create_time","status")
    count = jielongs.count()
    jielongs = jielongs[start:end]
    if count > end:
        has_next = True
    else:
        has_next = False

    jielong = []
    if jielongs:
        for j in jielongs:
            browse_num = j.browse_num
            orderlist,count = OrderService.order_list(jielong_id=j.id)
            total_price = OrderService.total_order_price(jielong_id=j.id)
            # order_total_price = total_price["order_num"]
            order_total_price = total_price
            if not order_total_price:
                order_total_price = "0.00"
            item = {
                "id":j.id,
                "title":j.title,
                "status":get_jielong_status(j.id),
                "create_time":get_time_span(UtilDateTime.utc2local(j.create_time)),
                "nick":get_covert_user_nickname(j.id,j.passport_user.wechatuser.nickname),
                "avatar_url":covert_avatar_url(j.passport_user.wechatuser.avatar_url),
                "info":"%s人浏览 , %s人参加，总收入%s元" % (browse_num,count,order_total_price)
            }
            jielong.append(item)

    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "has_next": has_next,
            "items": jielong
        }
    }
    return result

def get_join_jielong_order_by_user_id(user_id,page_no,page_size):
    order_list,count = OrderService.order_list(page_size=page_size,page_no=page_no,user_id=user_id)
    has_next = False if len(order_list) <= page_size else True
    jielong = []
    if len(order_list) > 0:
        for o in order_list:
            goods_info = []
            jielong_id = o["activity_id"]
            print(jielong_id)
            create_time = o["order_time"].strftime("%Y-%m-%d %H:%M:%S")
            pay_info = "已付款 : %s元" % (o["order_price"])
            goods = o["goods"]
            for g in goods:
                g_title = g["title"]
                g_sku_des = g["sku_desc"]
                g_buy_num = g["buy_num"]
                g_info = "%s(%s)x%s" % (g_title,g_sku_des,g_buy_num)
                goods_info.append(g_info)

            item = {
                "title":get_jielong_info_by_id(jielong_id),
                "create_time":create_time,
                "pay_info":pay_info,
                "goods_info":goods_info
            }
            jielong.append(item)

    result = {
        "meta": {
            "msg": "",
            "code": 0
        },
        "results": {
            "has_next": has_next,
            "items": jielong
        }
    }
    return result


def get_jielong_info_by_id(jielong_id):
    try:
        jielong = JieLong.objects.get(id = jielong_id)
        return jielong.title
    except JieLong.DoesNotExist as e:
        print(e)
        return ""

def get_jielong_status(jielong_id):
    current_date = datetime.now()
    try:
        jielong = JieLong.objects.get(id=jielong_id)
        jielong_begin_time = UtilDateTime.utc2local(jielong.begin_time)
        jielong_begin_time = UtilDateTime.timestr_to_datetime(jielong_begin_time)
        jielong_end_time = UtilDateTime.utc2local(jielong.end_time)
        jielong_end_time = UtilDateTime.timestr_to_datetime(jielong_end_time)
        if jielong.status != 1:
            if jielong_begin_time > current_date:
                return 2
            elif jielong_end_time < current_date:
                return 1
            else:
                return jielong.status
        else:
            return jielong.status
    except JieLong.DoesNotExist:
        return 1
    except Exception as e:
        print(e)

def get_covert_user_nickname(user_id,nickname):
    if not nickname or nickname == "":
        # nickname = "user_%s" % (user_id)
        nickname = "神秘来访者"
    return nickname

def covert_avatar_url(avatar_url):
    if not avatar_url or avatar_url == "":
        avatar_url = "https://i1.hemaweidian.com/hsupload/5222ae1ab0cda1244be08b6f174479ba51c0948793f42f92521e214c67790823_GA0mMZa.jpg"
    return avatar_url

def get_jielong_ids(user_id):
    '''
    获取用户创建和参与的活动id
    :param user_id:
    :return: c_ids,p_ids,m_ids
    '''
    c_jielongs = JieLong.objects.filter(passport_user_id=user_id).order_by("-create_time", "status")
    c_ids = []
    p_ids = []
    m_ids = []
    for c in c_jielongs:
        c_id = c.id
        c_ids.append(c_id)
        m_ids.append(c_id)
    p_jielongs = OrderService.order_queryset(user_id=user_id).values_list("activity_id", flat=True).distinct()
    for p in p_jielongs:
        p_id = int(p)
        p_ids.append(p_id)
        m_ids.append(p_id)

    a_user = JieLongUserRelation.objects.filter(passport_user_id=user_id,is_attention = 0)
    a_user_ids = []
    for u in a_user:
        a_user_ids.append(u.jielong.passport_user_id)
    a_user_ids = list(set(a_user_ids))
    a_jielongs = JieLong.objects.filter(passport_user_id__in=a_user_ids).order_by("-create_time", "status")
    a_ids = []
    for a in a_jielongs:
        a_ids.append(a.id)
        m_ids.append(a.id)

    s_user_ids = []
    # s_user = JieLongSpreadUserRelation.objects.filter(passport_user_id = user_id,status = 1)
    # for s in s_user:
    #     s_user_ids.append(s.invite_sponsor_id)
    # s_jielongs = JieLong.objects.filter(passport_user_id__in=s_user_ids)
    # s_ids = []
    # for s in s_jielongs:
    #     s_ids.append(s.id)
    #     m_ids.append(s.id)

    func = lambda x, y: x if y in x else x + [y]
    m_ids = reduce(func, [[], ] + m_ids)

    logger.info("get_jielong_ids user-info a_user_ids: %s;s_user_ids:%s" % (a_user_ids, s_user_ids))

    return c_ids,p_ids,m_ids

def get_jielong_label(jielong_id,c_ids,p_ids):
    if jielong_id in c_ids:
        return "我发布的"
    elif jielong_id in p_ids:
        return "我参与的"
    else:
        return ""