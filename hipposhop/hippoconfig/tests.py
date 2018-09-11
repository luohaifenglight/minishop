from django.test import TestCase, Client

# Create your tests here.
from hippoconfig.service import ConfigService
from hippoconfig.models import ServiceConfig, ApplicationConfig, PlatformConfig


class ConfigTestCase(TestCase):
    '''
    保留测试DB，不用每次都重新生成
    python manage.py test --keepdb
    python3 manage.py test hippoconfig --settings=hipposhop.settings.dev --keepdb

    '''
    def setUp(self):
        self.client = Client()
        self.add_default_config_value()

    def tearDown(self):
        pass

    def add_default_config_value(self):
        ApplicationConfig.objects.update_or_create(product_code='all', defaults={
            'product_name': 'all',
        })
        PlatformConfig.objects.update_or_create(platform_code='all', defaults={
            'platform_name': 'all',
        })


    def test_config_str(self):
        app_cfg = ApplicationConfig.objects.get(product_code='all')
        platform_cfg = PlatformConfig.objects.get(platform_code='all')

        ServiceConfig.objects.update_or_create(key="test_config_str", defaults={
            'name': 'test1',
            'value': 'test1',
            'status': 0,
            'app_config': app_cfg,
            'platform_config': platform_cfg,
        })

        result = ConfigService.get_config_str(key='test_config_str')
        self.assertEquals('test1', result, msg='get_config_str')

    def test_config_int(self):
        app_cfg = ApplicationConfig.objects.get(product_code='all')
        platform_cfg = PlatformConfig.objects.get(platform_code='all')

        ServiceConfig.objects.update_or_create(key="test_config_int", defaults={
            'name': 'test1',
            'value': '123',
            'status': 0,
            'app_config': app_cfg,
            'platform_config': platform_cfg,
        })

        result = ConfigService.get_config_int(key='test_config_int')
        self.assertEquals(123, result, msg='test_config_int')

