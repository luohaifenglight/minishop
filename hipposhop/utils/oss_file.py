# -*- coding: utf-8 -*-

import hashlib
import os
import platform
import urllib
# import urllib2

import oss2
import requests
from django.conf import settings
from datetime import datetime


'''
上传文件到OSS：
支持： 根据URL上传文件
       本地文件上传
'''
class OssFileUtil():
    path_hash_type = 2  # 1-根据hash确定目录； 2-根据时间生成目录，2018/03/16
    item_pic_base = 'itempic'
    url_with_host = False

    def __init__(self):
        self.base_dir = settings.BASE_DIR
        self.data_file_path = os.path.join(self.base_dir, 'data')
        # if not os.path.exists(self.data_file_path):
        #     os.makedirs(self.data_file_path)

        auth = oss2.Auth(settings.OSS_ACCESS_KEY, settings.OSS_ACCESS_SECRET)
        self.bucket = oss2.Bucket(auth, settings.OSS_END_POINT, settings.OSS_BUCKET_NAME)

    def upload_bytes(self, bytes_content, hash_file_name, file_suffix=".jpg"):
        try:
            hash_file_path = "%s%s" % (hash_file_name, file_suffix)
            result = self.bucket.put_object(hash_file_path, bytes_content, headers={'Content-Type': 'image/jpeg'})
            url = result.resp.response.url
            url = url.replace("http://hipposhop-pub.oss-cn-shenzhen.aliyuncs.com","https://i1.hemaweidian.com")
            return url
        except Exception as e:
            print(str(e))
            return None

    def upload_item_pic_from_url(self, url):
        #print("upload_item_pic_from_url:%s" % url)

        base = self.item_pic_base
        file_parts = os.path.splitext(url)
        if file_parts[1]:
            if file_parts[1].find("_") > 0:
                # 处理一些特殊的后缀，png_400x400
                file_suffix =  file_parts[1].split("_")[0]
            else:
                file_suffix = file_parts[1]
        else:
            # 默认，这个处理不全面， Todo
            file_suffix = ".jpg"

        hash_code = self._get_url_hash(url)
        hash_path = self._get_hash_path(hash_code)

        if platform.system() == "Windows":
            full_path = base + '/' + hash_path
            hash_file_name = full_path + "/" + hash_code + file_suffix
        else:
            full_path = os.path.join(base, hash_path)
            hash_file_name = os.path.join(full_path, hash_code + file_suffix)

        #print('hash_file_name=%s' % hash_file_name)
        try:
            input = requests.get(url)
            result = self.bucket.put_object(hash_file_name, input, headers={'Content-Type': 'image/jpeg'})
            #print('http status: {0}'.format(result.status))
            #print('request_id: {0}'.format(result.request_id))
            #print('ETag: {0}'.format(result.etag))

            if self.url_with_host:
                maked_url = self.bucket._make_url(settings.BUCKET_NAME, hash_file_name)
                url = urllib.unquote(maked_url).replace(settings.END_POINT_URL, settings.ALIYUN_OSS_CNAME_URL)
            else:
                url = hash_file_name
            return url
        except Exception as e:
            print(str(e))
            return None

    def upload_item_pic(self, filename):
        print("upload_item_pic:%s" % filename)
        if not os.path.isfile(filename):
            return False

        base = self.item_pic_base
        file_parts = os.path.splitext(filename)
        hash_code = self._get_file_hash(filename)
        hash_path = self._get_hash_path(hash_code)

        full_path = os.path.join(base, hash_path)
        hash_file_name = os.path.join(full_path, hash_code + file_parts[1])
        print('hash_file_name=%s' % hash_file_name)
        try:
            with open(filename, 'rb') as fileobj:
                self.bucket.put_object(hash_file_name, fileobj)

            maked_url = self.bucket._make_url(settings.BUCKET_NAME, hash_file_name)
            url = urllib.unquote(maked_url).replace(settings.END_POINT_URL, settings.ALIYUN_OSS_CNAME_URL)
            print(url)
            return url
        except Exception as e:
            print(str(e))
            return None

    def _get_hash_path(self, hash_name):
        if self.path_hash_type == 1:
            # 去hash值的第一位做为目录名称
            return hash_name[0:1]
        elif self.path_hash_type == 2:
            #根据时间生成hash目录，比如  2018/03/16
            cur_d = datetime.now().strftime("%Y/%m/%d")
            return cur_d
        else:
            return hash_name[0:1]

    def _get_file_hash(self, filepath, buffer=4096):
        """
            get hash value by assigned hashcode ,filepath with buffer
        """
        bs = None
        hashcode = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while True:
                bs = f.read(buffer)
                if not bs:
                    break
                else:
                    hashcode.update(bs)
        return hashcode.hexdigest()

    def _get_url_hash(self, url):
        hashcode = hashlib.sha256()
        hashcode.update(url)
        return hashcode.hexdigest()

    def get_remote_file_info(self, url, proxy=None):
        opener = urllib2.build_opener()
        if proxy:
            if url.lower().startswith('https://'):
                opener.add_handler(urllib2.ProxyHandler({'https': proxy}))
            else:
                opener.add_handler(urllib2.ProxyHandler({'http': proxy}))
        try:
            request = urllib2.Request(url)
            request.get_method = lambda: 'HEAD'
            response = opener.open(request)
            response.read()
        except Exception as e:  # 远程文件不存在
            return 0
        else:
            return dict(response.headers)

    def test(self):

        print("p=%s" % self.data_file_path)

        filename = os.path.join(self.data_file_path, '2.jpg')
        url = "http://file.17gwx.com/sqkb/coupon/2018/3/14/_1521011510377779556_400x400"
        url = "http://img.alicdn.com/imgextra/i1/1801358187/TB20NklbmJjpuFjy0FdXXXmoFXa_!!1801358187.jpg"
        #result = self.get_remote_file_info(url)
        #print(result)
        self.upload_item_pic_from_url(url)

