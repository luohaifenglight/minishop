from django.test import TestCase

# Create your tests here.
param_dict = {
        "nickname": "123456",
        "avatar_url": "456789"
    }
nickname = param_dict.get("nickname",None)
avatar_url = param_dict.get("avatar_url")
print(nickname)
param_dict = {}
if nickname:
    param_dict["nickname"] = nickname
if avatar_url:
    param_dict["avatar_url"] = avatar_url

print(param_dict)