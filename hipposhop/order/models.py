from django.db import models

# Create your models here.


from product.models import Product
from .orderlintcode import BaseOrderManager


class OrderUser(models.Model):
    """
    订单主表
    """
    trade_parent_id = models.BigIntegerField(verbose_name="父订单号", db_index=True)
    batch_id = models.BigIntegerField(verbose_name="批次号")

    total_price = models.DecimalField(verbose_name="总金额", max_length=100, max_digits=20, decimal_places=4, default=0)
    pay_price = models.DecimalField(verbose_name="支付金额", max_length=100, max_digits=20, decimal_places=4, default=0)
    pay_time = models.DateTimeField(verbose_name='订单付款时间', null=True, db_index=True)
    pay_account = models.CharField(verbose_name="付款账号", max_length=100, default="")
    pay_channel = models.CharField(verbose_name="支付渠道", help_text="alipay, wechat, other", max_length=20, default="wechat")

    status = models.CharField(verbose_name="订单状态", default="unpaid", max_length=20, help_text="paied, unpaid, cancel, settled")
    buyer_id = models.BigIntegerField(verbose_name="下单用户", db_index=True)
    seller_id = models.BigIntegerField(verbose_name="卖家", db_index=True)
    buyer_remark = models.CharField(verbose_name="买家备注", max_length=1000, default="")
    seller_remark = models.CharField(verbose_name="卖家备注", max_length=1000, default="")
    is_reward = models.IntegerField(verbose_name="是否获取奖励", default=0)
    spread_user_id = models.BigIntegerField(verbose_name="推广者", null=True, blank=True)
    commission = models.DecimalField(verbose_name="推广者获得的佣金金额", max_length=100, max_digits=20, decimal_places=4,
                                     default=0)

    address_id = models.BigIntegerField(verbose_name="收货地址", null=True, blank=True)
    activity_id = models.BigIntegerField(verbose_name="活动", db_index=True, null=True, blank=True)
    activity_name = models.CharField(verbose_name="活动名称", max_length=1000, default="")

    commission_rate = models.DecimalField(verbose_name="推广者获得的佣金比例", max_length=100, max_digits=20, decimal_places=4, default=0)
    tax_rate = models.DecimalField(verbose_name="推广者获得的佣金比例", max_length=100, max_digits=20, decimal_places=4, default=0.006)
    sell_price = models.DecimalField(verbose_name="卖家收益", max_length=100, max_digits=20, decimal_places=4,
                                     default=0)
    earning_time = models.DateTimeField(verbose_name='订单结算时间', null=True, db_index=True)

    remark = models.CharField(verbose_name="备注", max_length=1000, default="")
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    apply_refund_time = models.DateTimeField(verbose_name='订单申请退款时间', null=True, db_index=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    objects = BaseOrderManager()

    def __str__(self):
        return str(self.trade_parent_id)

    class Meta:
        verbose_name = "订单主表"
        verbose_name_plural = "订单主表"


class OrderDetail(models.Model):
    """
    订单子表
    """
    trade_id = models.BigIntegerField(verbose_name="订单号")
    trade_parent_id = models.BigIntegerField(verbose_name="父订单号", db_index=True)
    num_iid = models.BigIntegerField(verbose_name="商品ID")
    item_title = models.CharField(verbose_name="商品标题", max_length=1000)
    item_num = models.BigIntegerField(verbose_name="商品数量")
    price = models.DecimalField(verbose_name="单价", max_length=100, max_digits=20, decimal_places=4, default=0)

    remark = models.CharField(verbose_name="备注", max_length=1000, default="")
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    objects = BaseOrderManager()

    def __str__(self):
        return str(self.trade_id)

    class Meta:
        verbose_name = "订单子表"
        verbose_name_plural = "订单子表"


class Statement(models.Model):
    user_id = models.BigIntegerField(verbose_name="用户")
    money = models.DecimalField(verbose_name="金额", max_digits=20, decimal_places=4, default=0)
    account_type = models.IntegerField(verbose_name='账户类型', default=0) #choices=((0, 'app流水'), (1, 'oa流水'))
    type = models.IntegerField(verbose_name='类型收入或者指出', default=0) # 0收入 1支出
    desc = models.CharField(verbose_name="描述", max_length=1000, default="")
    desc1 = models.CharField(verbose_name="描述1", max_length=1000, default="")
    desc2 = models.CharField(verbose_name="描述2", max_length=1000, default="")
    desc3 = models.CharField(verbose_name="描述3", max_length=1000, default="")
    balance = models.DecimalField(verbose_name="余额", max_digits=20, decimal_places=4, default=0)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='时间')

    objects = BaseOrderManager()

    class Meta:
        verbose_name = "用户流水表"
        verbose_name_plural = "用户流水表"


# 提现表
class WithdrawCash(models.Model):
    user_id = models.BigIntegerField(verbose_name="用户")
    user_name = models.CharField(verbose_name="支付宝姓名", max_length=50, default="")
    money = models.DecimalField(verbose_name="体现金额", max_digits=20, decimal_places=4, default=0)
    status = models.IntegerField(verbose_name='状态0申请体现中，1体现成功，2体现失败', choices=((0, '申请提现中'), (1, '体现陈功'), (2, '体现失败')), default=0) # 0申请体现中，1体现成功，2体现失败
    apply_time = models.DateTimeField(auto_now_add=True, verbose_name='申请时间',)
    open_id = models.CharField(verbose_name="openid", max_length=50, default="")
    order_num = models.CharField(verbose_name="流水号", blank=True, max_length=50, default="")
    payment_no = models.CharField(verbose_name="微信流水号", blank=True, max_length=50, default="")
    remark = models.CharField(verbose_name="备注", blank=True, max_length=50, default="")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = "提现申请表"
        verbose_name_plural = "提现申请表"


class FreezeAssert(models.Model):
    user_id = models.BigIntegerField(verbose_name="用户")  #
    price = models.DecimalField(verbose_name="money", max_digits=20, decimal_places=4, default=0)
    reason = models.CharField(verbose_name="原因", default="REFUND", max_length=150)
    type = models.CharField(verbose_name="冻结类型", default="refund", max_length=50)
    relation_id = models.CharField(verbose_name="关联ID", default="", max_length=150)
    status = models.CharField(verbose_name="冻结状态", default="freeze", max_length=50) # unfreeze freeze

    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return str(self.user_id)

    class Meta:
        verbose_name = "资产冻结信息"
        verbose_name_plural = "资产冻结信息"

