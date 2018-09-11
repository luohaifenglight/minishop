from django.test import TestCase
from django.test import TestCase, Client

# Create your tests here.


class ProductTestCase(TestCase):
    '''
    保留测试DB，不用每次都重新生成
    python manage.py test product --keepdb
    python3 manage.py test product --settings=hipposhop.settings.dev --keepdb

    '''
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass




