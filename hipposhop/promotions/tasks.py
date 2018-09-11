# -*- coding: utf-8 -*-
from datetime import datetime
from celery import task

from payment.wechartpay import local2utc
from promotions.models import JieLong


def update_promotions():
    not_start_score = 20000
    starting_score = 40000
    end_score = 0
    current_time = datetime.now()
    current_time = local2utc(current_time)
    jielong = JieLong.objects.filter(begin_time__gt = current_time)
    if jielong:
        for j in jielong:
            # print("not start")
            # print(j.title)
            j.display_order = not_start_score
            j.save()

    jielonging = JieLong.objects.filter(begin_time__lte=current_time,end_time__gte=current_time)
    if jielonging:
        for j in jielonging:
            # print("starting")
            # print(j.title)
            j.display_order = starting_score
            j.save()

    jielongend = JieLong.objects.filter(end_time__lt=current_time)
    if jielongend:
        for j in jielongend:
            # print("end")
            # print(j.title)
            j.display_order = end_score
            j.status = 1
            j.save()

    jielongend = JieLong.objects.filter(status = 1)
    if jielongend:
        for j in jielongend:
            # print("end")
            # print(j.title)
            j.display_order = end_score
            j.save()

    return True

@task
def update_promotions_task():
    update_promotions()