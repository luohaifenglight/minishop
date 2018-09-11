from django.db import models

# Create your models here.


class WeChatPay(models.Model):
    # username = models.CharField(verbose_name="用户名", max_length=150, unique=True, )
    out_trade_no = models.CharField(verbose_name="交易订单号", max_length=150)
    order_id = models.CharField(verbose_name="订单号", max_length=150, default="")
    user_id = models.BigIntegerField(verbose_name="支付用户")  # 下单用户
    price = models.DecimalField(verbose_name="交易价格", max_digits=20, decimal_places=4, default=0)
    openid = models.CharField(verbose_name="openid", max_length=150)
    prepay_id = models.CharField(verbose_name="prepay_id", default="", max_length=150)
    result_code = models.CharField(verbose_name="result_code", default="", max_length=150)
    return_code = models.CharField(verbose_name="return_code", default="", max_length=150)
    err_code = models.CharField(verbose_name="err_code", default="", max_length=150)
    transaction_id = models.CharField(verbose_name="微信订单号", max_length=150, default="")
    time_end = models.CharField(verbose_name="交易完成时间", max_length=150, default="")
    total_fee = models.DecimalField(verbose_name="订单金额", max_digits=20, decimal_places=4, default=0)
    trade_state = models.CharField(verbose_name="订单状态", max_length=150, default="")
    ctime = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)

    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.openid

    class Meta:
        verbose_name = "微信支付信息"
        verbose_name_plural = "微信支付信息"


class WeChatRefund(models.Model):
    # username = models.CharField(verbose_name="用户名", max_length=150, unique=True, )
    out_refund_no = models.CharField(verbose_name="交易订单号", max_length=150)
    order_id = models.CharField(verbose_name="订单号", max_length=150, default="")
    user_id = models.BigIntegerField(verbose_name="支付用户")  # 下单用户
    price = models.DecimalField(verbose_name="交易价格", max_digits=20, decimal_places=4, default=0)
    result_code = models.CharField(verbose_name="result_code", default="", max_length=150)
    return_code = models.CharField(verbose_name="return_code", default="", max_length=150)
    err_code = models.CharField(verbose_name="err_code", default="", max_length=150)
    transaction_id = models.CharField(verbose_name="微信订单号", max_length=150, default="")
    refund_id = models.CharField(verbose_name="退款单号", max_length=150, default="")
    success_time = models.CharField(verbose_name="交易完成时间", max_length=150, default="")
    total_fee = models.DecimalField(verbose_name="标价金额", max_digits=20, decimal_places=4, default=0)
    refund_fee = models.DecimalField(verbose_name="申请退款金额", max_digits=20, decimal_places=4, default=0)
    settlement_refund_fee = models.DecimalField(verbose_name="退款金额", max_digits=20, decimal_places=4, default=0)
    ctime = models.DateTimeField(verbose_name="退款成功时间", null=True, blank=True)

    refund_recv_accout = models.CharField(verbose_name="refund_recv_accout", default="", max_length=150)
    refund_account = models.CharField(verbose_name="refund_account", default="", max_length=150)
    refund_request_source = models.CharField(verbose_name="refund_request_source", default="", max_length=150)
    out_trade_no = models.CharField(verbose_name="out_trade_no", default="", max_length=150)
    refund_status = models.CharField(verbose_name="refund_status", default="", max_length=150)

    refund_state = models.CharField(verbose_name="refund_state", default="", max_length=150) # "self"

    reason = models.CharField(verbose_name="退款原因", default="", max_length=150)
    fail_reason = models.CharField(verbose_name="退款失败原因", default="", max_length=150)

    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return str(self.refund_id)

    class Meta:
        verbose_name = "微信退款信息"
        verbose_name_plural = "微信退款信息"

