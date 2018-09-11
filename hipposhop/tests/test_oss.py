# -*- coding: utf-8 -*-

import configparser
import oss2



config_file = '../config/config_dev.ini'
config = configparser.ConfigParser()
ret = config.read(config_file)


#oss
oss_endpoint = config.get('oss', 'endpoint')
oss_key = config.get('oss', 'key')
oss_secret = config.get('oss', 'secret')


auth = oss2.Auth(oss_key, oss_secret)
service = oss2.Service(auth, oss_endpoint)

print([b.name for b in oss2.BucketIterator(service)])


