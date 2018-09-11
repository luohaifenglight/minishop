#! coding:utf-8

from Crypto.Cipher import AES


class AESCommon(object):
    @classmethod
    def encrypt(cls, data, key="HMWD_HMWD_AESKEY"):
        cryptor = AES.new(key, AES.MODE_ECB)
        pad = len(data) % 16
        if pad:
            data = data + chr(16 - pad) * (16 - pad)

        result = cryptor.encrypt(data)
        return result

    @classmethod
    def decrypt(cls, data, key="HMWD_HMWD_AESKEY"):
        cryptor = AES.new(key, AES.MODE_ECB)
        result = cryptor.decrypt(data)
        if isinstance(result, bytes):
            result = result.decode("utf-8")
        x = ord(result[-1])
        result = result[:len(result)-int(x)]
        return result