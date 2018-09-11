# ! coding:utf-8

from PIL import Image, ImageDraw, ImageFont
import qrcode
import hashlib
import requests as req
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.cache import cache


class CombineImage(object):

    QRCODE_URL = "http://hipposhop.hemaweidian.com/scheme/"

    @classmethod
    def produce_image(cls, base_img, tmp_img):
        base_img = base_img.resize((400, 400))
        region = tmp_img
        region_size = region.getbbox()
        max_box = base_img.getbbox()
        resizea = max_box[2] if max_box[2] < max_box[3] else max_box[3]
        if region_size[2] > resizea / 2 or region_size[2] > resizea / 2:
            d, h = int(resizea / 2), int(resizea / 2)
            region = region.resize((d, h))   
        #region = region.resize((box[2] - box[0], box[3] - box[1]))
        region_box = region.getbbox()
        #max_box = base_img.getbbox()
        print (region_box)
        print (max_box)
        a, b = int(max_box[2] / 4), int(max_box[3] / 4)
        c, d = a + region_box[2], b + region_box[3]
        copy_box = (a, b, c, d)
        base_img.paste(region, copy_box)
        base_img = cls._write_font(base_img, int(max_box[2] / 2), 10)
        # base_img.save("fgh.png")
        return base_img

    @classmethod
    def _write_font(cls, base_img, x, y, text="龙的传人"):
        draw = ImageDraw.Draw(base_img)
        x = x - int(len(text) * 10)
        font = ImageFont.truetype("df1.ttf", 20, encoding="unic")  # 设置字体
        draw.text((x, y), text, 'fuchsia', font)
        return base_img

    @classmethod
    def get_image_data(cls, img_src):
        response = req.get(img_src)
        if response.status_code != 200:
            raise Exception("图片不存在")
        image = Image.open(BytesIO(response.content))
        return image

    @classmethod
    def product_qrcode_image(cls, qurl):
        return qrcode.make(qurl).get_image()

    @classmethod
    def _get_bytes(cls, base_img):
        img_bytes = BytesIO()
        base_img.save(img_bytes, format='PNG')
        img_arrs = img_bytes.getvalue()
        return img_arrs

    @classmethod
    def produce_share_url(cls, img_src, qurl):
        base_image = cls.get_image_data(img_src)
        tmp_img = cls.product_qrcode_image(qurl)
        result_img = cls.produce_image(base_image, tmp_img)
        file_name = cls.get_file_name(img_src, qurl)
        content = cls._get_bytes(result_img)
        the_file = ContentFile(content, name=file_name)
        path = default_storage.save(name=file_name, content=the_file)
        return path

    @classmethod
    def get_file_name(cls, img_src, qurl):
        combine_name = "%s-%s" % (img_src, qurl)
        mystr = combine_name.encode("utf-8")
        mymd5 = hashlib.md5()
        mymd5.update(mystr)
        result = mymd5.hexdigest()
        result = "hsupload/%s.png" % result
        return result

    @classmethod
    def share_image(cls, jielong_id, user_id):
        from promotions.models import JieLong
        from .fileservice import get_full_path
        jielong = JieLong.objects.get(id=jielong_id)
        product_image = jielong.small_images.strip().split(" ")[0]
        if not product_image:
            raise Exception("no smalle images")
        product_image_url = get_full_path(product_image)
        if product_image.startswith("http://") or product_image.startswith("https://"):
            product_image_url = product_image
        qrcode_url = "%s?user_id=%s&activity=%s" % (cls.QRCODE_URL, user_id, jielong_id)
        file_name = cls.get_file_name(product_image_url, qrcode_url)
        path = cache.get(file_name)
        print (product_image_url)
        print (qrcode_url)
        if not path:
            path = cls.produce_share_url(product_image_url, qrcode_url)
            cache.set(file_name, path)
        return get_full_path(path)

    @classmethod
    def share_qrcode_url(cls, jielong_id, user_id):
        qrcode_url = "%s?user_id=%s&activity=%s" % (cls.QRCODE_URL, user_id, jielong_id)
        return qrcode_url
