# -*- coding: utf-8 -*-

import time
import pytz


from datetime import datetime,timedelta

'''

now = datetime.datetime.now()

#本周第一天和最后一天
this_week_start = now - timedelta(days=now.weekday())
this_week_end = now + timedelta(days=6-now.weekday())
 
#上周第一天和最后一天
last_week_start = now - timedelta(days=now.weekday()+7)
last_week_end = now - timedelta(days=now.weekday()+1)
 
#本月第一天和最后一天
this_month_start = datetime.datetime(now.year, now.month, 1)
this_month_end = datetime.datetime(now.year, now.month + 1, 1) - timedelta(days=1)
 
#上月第一天和最后一天
last_month_end = this_month_start - timedelta(days=1)
last_month_start = datetime.datetime(last_month_end.year, last_month_end.month, 1)
 
#本季第一天和最后一天
month = (now.month - 1) - (now.month - 1) % 3 + 1
this_quarter_start = datetime.datetime(now.year, month, 1)
this_quarter_end = datetime.datetime(now.year, month + 3, 1) - timedelta(days=1)
 
#上季第一天和最后一天
last_quarter_end = this_quarter_start - timedelta(days=1)
last_quarter_start = datetime.datetime(last_quarter_end.year, last_quarter_end.month - 2, 1)
 
#本年第一天和最后一天
this_year_start = datetime.datetime(now.year, 1, 1)
this_year_end = datetime.datetime(now.year + 1, 1, 1) - timedelta(days=1)
 
#去年第一天和最后一天
last_year_end = this_year_start - timedelta(days=1)
last_year_start = datetime.datetime(last_year_end.year, 1, 1)
　　
'''

class UtilDateTime():
    '''
        日期、时间处理工具类
    '''

    __local_tz = pytz.timezone('Asia/Chongqing')

    @staticmethod
    def local_to_utc_format(local_time, utc_format='%Y-%m-%dT%H:%MZ'):
        """
        当前时间转为utc时间格式化输出
        :param local_time: 如，datetime.datetime.now()
        :param utc_format:
        :return:
        """
        local_tz = pytz.timezone('Asia/Chongqing')
        local_dt = local_tz.localize(local_time, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.strftime(utc_format)


    @staticmethod
    def local_to_utc(local_time_str, utc_format='%Y-%m-%dT%H:%MZ'):
        # 本地时间转换为UTC

        local_format = "%Y-%m-%d %H:%M:%S"
        #time_str = time.strftime(local_format, time.localtime(local_ts))
        dt = datetime.strptime(local_time_str, local_format)
        local_dt = UtilDateTime.__local_tz.localize(dt, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.strftime(utc_format)

    @staticmethod
    def utc2local(utc_st,local_format="%Y-%m-%d %H:%M:%S"):
        ####UTC时间转本地时间（+8: 00）############
        now_stamp = time.time()
        local_time = datetime.fromtimestamp(now_stamp)
        utc_time = datetime.utcfromtimestamp(now_stamp)
        offset = local_time - utc_time
        local_st = utc_st + offset
        return local_st.strftime(local_format)

    @staticmethod
    def utc2local2m(utc_st,local_format="%Y-%m-%d %H:%M"):
        ####UTC时间转本地时间（+8: 00）############
        now_stamp = time.time()
        local_time = datetime.fromtimestamp(now_stamp)
        utc_time = datetime.utcfromtimestamp(now_stamp)
        offset = local_time - utc_time
        local_st = utc_st + offset
        return local_st.strftime(local_format)

    @staticmethod
    def timestamp2datetime(timestamp, convert_to_local=False):
        ''' Converts UNIX timestamp to a datetime object. '''
        utc_format = '%Y-%m-%dT%H:%MZ'
        if isinstance(timestamp, (int, float)):
            dt = datetime.utcfromtimestamp(timestamp)
            if convert_to_local: # 是否转化为本地时间
                dt = dt + timedelta(hours=8) # 中国默认时区
            local_dt = UtilDateTime.__local_tz.localize(dt, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            return utc_dt.strftime(utc_format)

    @staticmethod
    def datestr_to_datetime(date_str):
        '''
        日期字符串转datetime类型
        :param date_str:   2018-04-20
        :return:
        '''
        date_str = date_str.replace('\'', '')
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt

    @staticmethod
    def timestr_to_datetime(time_str):
        '''
        时间字符串转datetime类型
        :param time_str:   2018-04-20 00:00:00
        :return:
        '''
        dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        return dt

    @staticmethod
    def datetime_to_str(input_dt):
        if input_dt is None:
            return ''
        t_format = '%Y-%m-%d %H:%M:%S'
        return input_dt.strftime(t_format)

