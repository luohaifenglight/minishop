# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals

from django.core.mail import EmailMessage


class ReportUtil(object):

    @staticmethod
    def send_mail(subject, content, to_address, attach_file=None):
        # to_address:
        #   email address list, such as ['dahui@hemaweidian.com',  '112434232qq.com]
        attach_file_list = attach_file.split(",")
        try:
            email = EmailMessage(subject=subject, body=content, to=to_address)
            email.content_subtype = "html"
            for file in attach_file_list:
                email.attach_file(file)
            res = email.send()
            code, msg = 0, "success"
        except Exception as e:
            code, msg = 90006, "%s" % e
        return code, msg
