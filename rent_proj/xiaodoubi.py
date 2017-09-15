import requests
import json

myRequests = requests.session()
headers = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36'}
#url = 'http://www.xiaodoubi.com/bot/chat.php'
url = 'http://api.qingyunke.com/api.php'

while True:
	word = raw_input("input some word ")
	if word == 'q':
		break
	#params = {'chat':word}
	params = {'key':'free','appid':0,'msg':word}
	myRequests.headers.update(headers)
	r = myRequests.post(url,params=params)
	r.encoding = 'utf-8'
	#r = requests.post(url,data={'key':'free','appid':0,'msg':word})
	strmap = json.loads(r.content)
	print(r.content)
	print(strmap['content'])
	print(type(r.content))