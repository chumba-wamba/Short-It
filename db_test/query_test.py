import sys
sys.path.insert(0, 'E:\Projects\Short-It')

from datetime import datetime
from json import loads, dumps
from short_it.models import URL, User
from short_it import db


url_test = URL.objects(shortened="test1")
if len(url_test) == 1 and url_test[0].shortened == "test1":
    url_test[0].update(inc__counter=1)
    url_test[0].update(push__date_array=datetime.utcnow)
print(url_test[0].counter)
print(url_test[0].date_array)

user_nisarg42 = User.objects(user_name="nisarg42")
print(user_nisarg42)
