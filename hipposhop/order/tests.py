from django.test import TestCase
from .orderservice import OrderService

# Create your tests here.


class OrderTestCase(TestCase):

    def setUp(self):
        print ("==start-set-up====")

    def test_create_order(self):
        userid = 1
        order_dict = {
            "jielong_id": 1,
            "goods": [{
                "id": 1,
                "sku_desc": "规格",
                "product_num": 2
            },
                {
                    "id": 2,
                    "sku_desc": "规格",
                    "product_num": 3
                },
            ],
            "spread_user_id": 1
        }
        jielong_id = order_dict.get("jielong_id")
        goods = order_dict.get("goods")
        spread_user = order_dict.get("spread_user_id")
        o = OrderService(userid)
        order_id = o.create_order(jielong_id, spread_user, goods)
        print (order_id)

    def tearDown(self):
        print ("==end-test====")
