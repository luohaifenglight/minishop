import json
from datetime import datetime, time

from django.test import TestCase

# Create your tests here.
from utils.date_util import UtilDateTime

current_date = datetime.now()
time_str = "2018-09-09 12:00:00"
dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
print(type(dt))

print(current_date.strftime("%Y-%m-%d %H:%M"))

