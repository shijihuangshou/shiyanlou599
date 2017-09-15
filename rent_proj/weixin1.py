# -*- coding:utf-8 -*-
import requests
import re
import os
import subprocess
import time
import sys
import xml.dom.minidom
import json
import threading
import math
import urllib2
import random
import multiprocessing
import io
from lxml import html
from urlparse import urlparse
from collections import defaultdict
DEBUG = True
MAX_GROUP_NUM = 2
INTERFACE_CALLING_INTERVAL = 5
MAX_PROGRESS_LEN = 50
BaseRequest = {}
def catchKeyboardInterrupt(fn):
	def wrapper(*args):
		try:
			return fn(*args)
		except KeyboardInterrupt:
			print('\n 强制退出程序')
	return wrapper
def responseState(func, BaseResponse):
	ErrMsg = BaseResponse['ErrMsg']
	Ret = BaseResponse['Ret']
	if DEBUG or Ret != 0:
		print('func: %s, Ret: %d, ErrMsg: %s' % (func, Ret, ErrMsg))
	if Ret != 0:
		return False
	return True
class WebWeiXin(object):
	def __init__(self):
		self.tip = 0
		self.uuid = ''
		self.base_uri = ''
		self.redirect_uri = ''
		self.push_uri = ''
		self.skey = ''
		self.wxsid = ''
		self.wxuin = ''
		self.pass_ticket = ''
		self.deviceId = 'e000000000000000'
		self.myRequests = requests.session()
		headers = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36'}
		self.myRequests.headers.update(headers)
		self.QRImagePath = ''
		self.BaseRequest = {}
		self.My=[]
		self.SyncKey=[]
		self.SyncKeyStr = ''
		self.MemberList = []
		self.ContactList = []  # 好友
		self.GroupList = []  # 群
		self.GroupMemeberList = []  # 群友
		self.PublicUsersList = []  # 公众号／服务号
		self.SpecialUsersList = []  # 特殊账号
		self.memberCount = 0
		self.lastCheckTs = 0
		self.autoReplyMode = False
		self.autoOpen = True
		self.saveFolder = os.path.join(os.getcwd(), 'saved')
		self.saveSubFolders = {'webwxgeticon': 'icons', 'webwxgetheadimg': 'headimgs', 'webwxgetmsgimg': 'msgimgs',
						'webwxgetvideo': 'videos', 'webwxgetvoice': 'voices', '_showQRCodeImg': 'qrcodes'}
		
	def responseState(self,func, BaseResponse):
		ErrMsg = BaseResponse['ErrMsg']
		Ret = BaseResponse['Ret']
		if DEBUG or Ret != 0:
			print('func: %s, Ret: %d, ErrMsg: %s' % (func, Ret, ErrMsg))
		if Ret != 0:
			return False
		return True
		
	def getUUID(self):
		url = 'https://login.weixin.qq.com/jslogin'
		params =  {
			'appid': 'wx782c26e4c19acffb',
			'fun': 'new',
			'lang': 'zh_CN',
			'_': int(time.time()),
		}
		
		r = self.myRequests.get(url=url,params=params)
		r.encoding = 'utf-8'
		data = r.text
		regx =  r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
		pm = re.search(regx,data)
		code = pm.group(1)
		self.uuid = pm.group(2)
		if code == '200':
			return True
		else:
			return False
			
	def showQRImage(self):
		if self.uuid == '':
			return False
		
		url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
		params = {
		't': 'webwx',
		'_': int(time.time()),
		}
		self.tip = 1
		r = self.myRequests.get(url=url,params=params)
		self.QRImagePath = os.path.join(os.getcwd(), 'qrcode.jpg')
		f = open(self.QRImagePath,'wb')
		f.write(r.content)
		f.close()
		time.sleep(1)
		if sys.platform.find('linux') >= 0:
			subprocess.call(['xdg-open',self.QRImagePath])
		print('请使用二维码登录')
		return True
			
	def waitForLogin(self):
		url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
		self.tip, self.uuid, int(time.time()))
		r = self.myRequests.get(url=url)
		r.encoding = 'utf-8'
		data = r.text
		regx = r'window.code=(\d+);'
		pm = re.search(regx,data)
		code = pm.group(1)
		if code == '201':
			print('成功扫描，请在手机上点击确认登录')
			self.tip = 0
		elif code == '200':
			print('正在登录。。')
			regx = r'window.redirect_uri="(\S+?)";'
			pm = re.search(regx,data)
			self.redirect_uri = pm.group(1)+'&fun=new'
			#print(self.redirect_uri)
			self.base_uri = self.redirect_uri[:self.redirect_uri.rfind('/')]
			services = [
				('wx2.qq.com', 'webpush2.weixin.qq.com'),
				('qq.com', 'webpush.weixin.qq.com'),
				('web1.wechat.com', 'webpush1.wechat.com'),
				('web2.wechat.com', 'webpush2.wechat.com'),
				('wechat.com', 'webpush.wechat.com'),
				('web1.wechatapp.com', 'webpush1.wechatapp.com'),
			]
			self.push_uri = self.base_uri
			for (searchUrl,pushUrl) in services:
				if self.base_uri.find(searchUrl) >= 0:
					self.push_uri = 'https://%s/cgi-bin/mmwebwx-bin' % pushUrl
					break
		else:
			print('waitForLogin %s'%code)
		return code
	def login(self):
		r = self.myRequests.get(self.redirect_uri)
		r.encoding = 'utf-8'
		data = r.text
		print('login()....')
		print(self.redirect_uri)
		print(type(data))
		doc = xml.dom.minidom.parseString(data)
		root = doc.documentElement
		for node in root.childNodes:
			if node.nodeName == 'skey':
				self.skey = node.childNodes[0].data
			elif node.nodeName == 'wxsid':
				self.wxsid = node.childNodes[0].data
			elif node.nodeName == 'wxuin':
				self.wxuin = node.childNodes[0].data
			elif node.nodeName == 'pass_ticket':
				self.pass_ticket = node.childNodes[0].data
		if not all((self.skey, self.wxsid, self.wxuin, self.pass_ticket)):
			return False
			
		self.BaseRequest = {
			'Uin': int(self.wxuin),
			'Sid': self.wxsid,
			'Skey': self.skey,
			'DeviceID': self.deviceId,
		}
		return True
	def webwinit(self):
		url = (self.base_uri+ 
		'/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
			self.pass_ticket, self.skey, int(time.time())) )
		params = {'BaseRequest': self.BaseRequest}
		headers = {'content-type':'application/join; charset=UTF-8'}
		r = self.myRequests.post(url = url,data = json.dumps(params),headers=headers)
		r.encoding = 'utf-8'
		data = r.json()
		if DEBUG:
			f = open(os.path.join(os.getcwd(),'webwinit.json'),'w')
			f.write(r.content)
			f.close()
		dic = data
		self.ContactList = dic['ContactList']
		self.My = dic['User']
		self.SyncKey = dic['SyncKey']
		SyncKeyItems =['%s_%s' % (item['Key'], item['Val'])
					for item in self.SyncKey['List']]
		self.SyncKeyStr = '|'.join(SyncKeyItems)
		state = responseState('webwinit',dic['BaseResponse'])
		return state
		
	def webwxstatusnotify(self):
		url = self.base_uri + \
			'/webwxstatusnotify?lang=zh_CN&pass_ticket=%s' % (self.pass_ticket)
		params = {
			'BaseRequest': self.BaseRequest,
			"Code": 3,
			"FromUserName": self.My['UserName'],
			"ToUserName": self.My['UserName'],
			"ClientMsgId": int(time.time())
		}
		r = self.myRequests.post(url,data = json.dumps(params))
		dic = r.json()
		return dic['BaseResponse']['Ret'] == 0
	def webwxgetcontact(self):
		url = (self.base_uri+
			'/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
			self.pass_ticket,self.skey,int(time.time())))
		headers = {'content-type': 'application/json; charset=UTF-8'}
		r = self.myRequests.post(url=url,headers=headers)
		r.encoding='utf-8'
		data = r.json()
		if DEBUG:
			f = open(os.path.join(os.getcwd(), 'webwxgetcontact.json'), 'w')
			f.write(r.content)
			f.close()
		dic = data
		self.MemberList = dic['MemberList']
		self.MemberCount = dic['MemberCount']
		SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync", "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp", "facebookapp", "masssendapp",
					"meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder", "weixinreminder", "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts", "notification_messages", "wxitil", "userexperience_alarm"]
		ContactList = self.MemberList[:]
		for i in range(len(ContactList)-1,-1,-1):
			Member = ContactList[i]
			if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
				self.PublicUsersList.append(Member)
				ContactList.remove(Member)
			elif Member['UserName'] in SpecialUsers:  # 特殊账号
				self.SpecialUsersList.append(Member)
				ContactList.remove(Member)
			elif Member['UserName'].find('@@') != -1:  # 群聊
				self.GroupList.append(Member)
				ContactList.remove(Member)
			elif Member['UserName'] == self.My['UserName']:  # 自己
				ContactList.remove(Member)
		self.ContactList = ContactList
		return True
	def webwxbatchgetcontact(self):
		url = self.base_uri + \
			'/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' % (
				int(time.time()), self.pass_ticket)
		headers = {'content-type': 'application/json; charset=UTF-8'}
		params = {
			'BaseRequest': self.BaseRequest,
			'Count':len(self.GroupList),
			'List':[{'UserName':g['UserName'],"EncryChatRoomId":""} for g in self.GroupList]
		}
		r = self.myRequests.post(url=url,headers=headers,data= json.dumps(params))
		r.encoding='utf-8'
		data = r.json()
		if DEBUG:
			f = open(os.path.join(os.getcwd(), 'webwxbatchgetcontact.json'), 'w')
			f.write(r.content)
			f.close()
		dic = data
		ContactList = dic["ContactList"]
		ContactCount = dic['Count']
		for i in xrange(len(ContactList)-1,-1,-1):
			Contact = ContactList[i]
			MemberList = Contact['MemberList']
			for member in MemberList:
				self.GroupMemeberList.append(member)
		return True
	
	def synccheck(self):
		url = self.push_uri + '/synccheck?'
		print('synccheck')
		print(self.SyncKey)
		print(self.SyncKeyStr)
		#print(url)
		params = {
			'skey': self.BaseRequest['Skey'],
			'sid': self.BaseRequest['Sid'],
			'uin': self.BaseRequest['Uin'],
			'deviceId': self.BaseRequest['DeviceID'],
			'synckey': self.SyncKeyStr,
			'r': int(time.time()),
		}
		r = self.myRequests.get(url,params=params)
		r.encoding = 'utf-8'
		data = r.text
		regx = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
		pm = re.search(regx, data)
		retcode = pm.group(1)
		selector = pm.group(2)
		return [retcode,selector]
		
	def webwxsync(self):
		url = self.base_uri + '/webwxsync?lang=zh_CN&skey=%s&sid=%s&pass_ticket=%s' % (
			self.BaseRequest['Skey'], self.BaseRequest['Sid'], self.pass_ticket)
		params = {
		'BaseRequest': self.BaseRequest,
		'SyncKey': self.SyncKey,
		'rr': ~int(time.time()),
		}
		
		r = self.myRequests.post(url=url,data=json.dumps(params))
		r.encoding = 'utf-8'
		
		if DEBUG:
			print('webwxsync')
			print(r)
			print(type(r))
		data = r.json()
		
		dic = data
		if dic['BaseResponse']['Ret'] == 0:
			self.SyncKey = dic['SyncKey']
			SyncKeyItems =['%s_%s' % (item['Key'], item['Val']) for item in self.SyncKey['List']]
			self.SyncKeyStr = '|'.join(SyncKeyItems)
		return dic
		
	def listenMsgMode(self):
		print('进入消息监听模式...成功')
		playWeChat = 0
		redEnvelope = 0
		while True:
			self.lastCheckTs = time.time()
			[retcode, selector] = self.synccheck()
			if DEBUG:
				print('retcode: %s, selector: %s'%(retcode,selector))
			if retcode == '1100':
				print('你在手机上登出了微信')
				break
			if retcode == '1101':
				print('你在其它地方登陆了微信')
				break
			if retcode == '0':
				if selector == '2':
					r = self.webwxsync()
					if r is not None:
						self.handleMsg(r)
					elif selector == '6':
						redEnvelope += 1
						print('收到类似红包消息 %d 次'%redEnvelope)
					elif selector == '7':
						playWeChat += 1
						print('你在手机上玩微信被发现%d 次'%playWeChat)
						r = self.webwxsync()
					elif selector == '0':
						time.sleep(1)
			if (time.time() - self.lastCheckTs) <= 20:
				time.sleep(time.time() - self.lastCheckTs)
				
	def handleMsg(self,r):
		for msg in r['AddMsgList']:
			print('你有新的消息，注意查收')
			if DEBUG:
				fn = 'msg' + str(int(random.random()*100))+ '.json'
				f = open(os.path.join(os.getcwd(),fn),'w')
				f.write(json.dumps(msg))
			msgType = msg['MsgType']
			name = self.getUserRemarkName(msg['FromUserName'])
			content = msg['Content'].replace('&lt;','<').replace('&gt;','>')
			msgid = msg['MsgId']
			print("handleMsg msgType %s"%str(msgType))
			if msgType == 1:
				raw_msg = {'raw_msg': msg}
				self._showMsg(raw_msg)
				if self.autoReplyMode:
					ans = self._qingyunke(content) + '\n[自动回复]'
					'''
					if self.webwxsendmsg(ans,msg['FromUserName']):
						print('自动回复: ' + ans)
					else:
						print('自动回复失败')
					'''
			elif msgType == 3:
				image = self.webwxgetmsgimg(msgid)
				raw_msg = {'raw_msg': msg,
					'message': '%s 发送了一张图片: %s' % (name, image)}
				self._showMsg(raw_msg)
				self._safe_open(image)
			elif msgType == 34:
				'''
				voice = self.webwxgetvoice(msgid)
				raw_msg = {'raw_msg':msg,
						'message':'%s发来一段语音: %s'%(name,image)}
				self._showMsg(raw_msg)
				self._safe_open(voice)
				'''
				pass
			elif msgType == 42:
				info = msg['RecommendInfo']
				print('%s 发送一张名片'%name)
				print ('=========================')
				print ('= 昵称: %s' % info['NickName'])
				print ('= 微信号: %s' % info['Alias'])
				print ('= 地区: %s %s' % (info['Province'], info['City']))
				print ('= 性别: %s' % ['未知', '男', '女'][info['Sex']])
				print ('=========================')
				raw_msg = {'raw_msg': msg, 'message': '%s 发送了一张名片: %s' % (
					name.strip(), json.dumps(info))}
				self._showMsg(raw_msg)
			elif msgType == 47:
				#print('msgType == 47 %s'%content)
				
				url = self._searchContent('cdnurl',content)
				raw_msg = {'raw_msg':msg,
						'message':'%s 发了一个动画表情，点击下面链接查看: %s' % (name, url)}
				self._showMsg(raw_msg)
				self._safe_open(url)
				
			elif msgType == 49:
				appMsgType = defaultdict(lambda:"")
				appMsgType.update({5:'链接',3:'音乐',7:'微博'})
				print ('%s 分享了一个%s:' % (name, appMsgType[msg['AppMsgType']]))
				print ('=========================')
				print ('= 标题: %s' % msg['FileName'])
				print ('= 描述: %s' % self._searchContent('des', content, 'xml'))
				print ('= 链接: %s' % msg['Url'])
				print ('= 来自: %s' % self._searchContent('appname', content, 'xml'))
				print ('=========================')
				card = {
					'title': msg['FileName'],
					'description': self._searchContent('des', content, 'xml'),
					'url': msg['Url'],
					'appname': self._searchContent('appname', content, 'xml')
				}
				raw_msg = {'raw_msg': msg, 'message': '%s 分享了一个%s: %s' % (
					name, appMsgType[msg['AppMsgType']], json.dumps(card))}
				self._showMsg(raw_msg)
			elif msgType == 51:
				raw_msg = {'raw_msg': msg, 'message': '[*] 成功获取联系人信息'}
				self._showMsg(raw_msg)
			elif msgType == 62:
				voideo = self.webwxgetvideo(msgid)
				raw_msg = {'raw_msg':msg,
							'message':'%s 发了一段小视频: %s' % (name, video)}
				self._showMsg(raw_msg)
				self._safe_open(video)
			elif msgType == 10002:
				raw_msg = {'raw_msg': msg, 'message': '%s 撤回了一条消息' % name}
				self._showMsg(raw_msg)
			else:
				raw_msg = {
					'raw_msg': msg, 'message': '[*] 该消息类型为: %d，可能是表情，图片, 链接或红包' % msg['MsgType']}
				self._showMsg(raw_msg)
	def getUserRemarkName(self,id):
		name = '未知群' if id[:2] == '@@' else '陌生人'
		if id == self.My['UserName']:
			return self.My['NickName']
		if id[:2] == '@@':
			name = self.getGroupName(id)
		else:
			for member in self.SpecialUsersList:
				if member['UserName'] == id:
					name = member['RemarkName'] if member[
						'RemarkName'] else member['NickName']
			for member in self.PublicUsersList:
				if member['UserName'] == id:
					name = member['RemarkName'] if member[
						'RemarkName'] else member['NickName']
			for member in self.ContactList:
				if member['UserName'] == id:
					name = member['RemarkName'] if member[
						'RemarkName'] else member['NickName']
			for member in self.GroupMemeberList:
				if member['UserName'] == id:
					name = member['DisplayName'] if member[
						'DisplayName'] else member['NickName']
		return name
	def getGroupName(self,id):
		name = '未知群'
		for member in self.GroupList:
			if member['UserName'] == id:
				name = member['NickName']
		return name
		
	def getUserID(self,name):
		for member in self.MemberList:
			if name == member['RemarkName'] or name == member['NickName']:
				return member['UserName']
		return None
		
	def webwxsendmsg(self,word,to='filehelper'):
		url = self.base_uri + \
			'/webwxsendmsg?pass_ticket=%s' % (self.pass_ticket)
		clientMsgId = str(int(time.time() * 1000)) + \
			str(random.random())[:5].replace('.','')
			
		params = {
			'BaseRequest': self.BaseRequest,
			'Msg': {
				"Type": 1,
				"Content": self._transcoding(word),
				"FromUserName": self.My['UserName'],
				"ToUserName": to,
				"LocalID": clientMsgId,
				"ClientMsgId": clientMsgId
			}
		}
		headers = {'content-type': 'application/json; charset=UTF-8'}
		data = json.dumps(params,ensure_ascii=False).encode('utf-8')
		r = self.myRequests.post(url,data=data,headers=headers)
		r.encoding = 'utf-8'
		dic = r.json()
		return dic['BaseResponse']['Ret'] == 0
		
	def webwxgetmsgimg(self, msgid):
		url = self.base_uri + \
			'/webwxgetmsgimg?MsgID=%s&skey=%s' %(msgid,self.skey)
		r = self.myRequests.get(url)
		fn = 'img_' + msgid + '.jpg'
		#fn = os.path.join(os.getcwd(),fn)
		return self._saveFile(fn,r.content,'webwxgetmsgimg')
		
	def webwxgetvideo(self, msgid):
		url = self.base_uri + \
			'/webwxgetvideo?msgid=%s&skey=%s' % (msgid, self.skey)
		headers = {'content-type': 'application/json; charset=UTF-8','Range':'bytes=0-'}
		r = self.myRequests.get(url,headers=headers)
		fn = 'video_' + msgid + '.mp4'
		return self._saveFile(fn,r.content,'webwxgetvideo')
	def webwxgetvoice(self, msgid):
		url = self.base_uri + \
			'/webwxgetvoice?msgid=%s&skey=%s' % (msgid, self.skey)
		headers = {'content-type': 'application/json; charset=UTF-8','Range':'bytes=0-'}
		r = self.myRequests.get(url,headers=headers)
		fn = 'voice_' + msgid + '.mp3'
		return self._saveFile(fn,r.content,'webwxgetvoice')
		
	def sendMsg(self,name,word,isfile=False):
		id = self.getUserID(name)
		if id:
			if isfile:
				with open(word,'r') as f:
					for line in f.readline():
						line = line.replace('\n','')
						self._echo('->'+name+': '+line)
						if self.webwxsendmsg(line,id):
							print(' 成功发送')
						else:
							print('发送失败')
						time.sleep(1)
			else:
				if self.webwxsendmsg(word,id):
					print('消息发送成功')
				else:
					print('消息发送失败')
		else:
			print('此用户不存在')
			
	def sendMsgToAll(self,word):
		for contact in self.ContactList:
			name = contact['RemarkName'] if contact[
				'RemarkName'] else contact['NickName']
			id = contact['UserName']
			self._echo('->'+ name + ': '+word)
			if self.webwxsendmsg(word,id):
				print(' 成功发送 ')
			else:
				print(' 发送失败 ')
			time.sleep(1)
			
	def sendImg(self,name,file_name):
		pass
		
	def sendEmotion(self,name,file_name):
		pass
			
	def _echo(self,str):
		sys.stdout.write(str)
		sys.stdout.flush()
	def _run(self,str,func,*args):
		self._echo(str)
		if func(*args):
			print("%s...成功"%(str))
		else:
			print("%s...失败"%(str))
			exit()
	def _showMsg(self,message):
		srcName = None
		dstName = None
		groupName = None
		content = None
		
		msg = message
		if msg['raw_msg']:
			srcName = self.getUserRemarkName(msg['raw_msg']['FromUserName'])
			dstName = self.getUserRemarkName(msg['raw_msg']['ToUserName'])
			content = msg['raw_msg']['Content'].replace('&lt;','<').replace('&gt;','>')
			message_id = msg['raw_msg']['MsgId']
			
			if content.find('http://weixin.qq.com/cgi-bin/redirectforward?args=') != -1:
				data = self._get(content).decode('gbk').encode('utf-8')
				pos = self._searchContent('title',data,'xml')
				tree = html.fromstring(self._get(content))
				url = tree.xpath('//html/body/div/img')[0].attrib['src']
				
				for item in urlparse(url).query.split('&'):
					if item.split('=')[0] == 'center':
						loc = item.split('=')[-1:]
				content = '%s 发送了一个 位置消息 - 我在 [%s](%s) @ %s]' % (
					srcName, pos, url, loc)
				
			if msg['raw_msg']['ToUserName'] == 'filehelper':
				dstName = '文件传输助手'
			if msg['raw_msg']['FromUserName'][:2] == '@@':
				if re.search(":<br/>",content,re.IGNORECASE):
					[people,content] = content.split(':<br/>')
					groupName = srcName
					srcName = self.getUserRemarkName(people)
					dstName = 'GROUP'
				else:
					groupName = srcName
					srcName = 'SYSTEM'
			elif msg['raw_msg']['ToUserName'][:2] == '@@':
				groupName = dstName
				dstName = 'GROUP'
			
			if content == '收到红包，请在手机上查看':
				msg['message'] = content
				
			if 'message' in msg.keys():
				content = msg['message']
				
		if groupName != None:
			print ('%s |%s| %s -> %s: %s' % (message_id, groupName.strip(), srcName.strip(), dstName.strip(), content.replace('<br/>', '\n')))
		else:
			print ('%s %s -> %s: %s' % (message_id, srcName.strip(), dstName.strip(), content.replace('<br/>', '\n')))
			
	
	def _get(self,url,api=None):
		request = urllib2.Request(url = url)
		request.add_header('Referer','https://wx.qq.com/')
		if api == 'webwxgetvoice':
			request.add_header('Range', 'bytes=0-')
		if api == 'webwxgetvideo':
			request.add_header('Range', 'bytes=0-')
		response = urllib2.urlopen(request)
		data = response.read()
		return data
		
	def _searchContent(self, key,content,fmat='attr'):
		if fmat == 'attr':
			pm = re.search(key+'\s?=\s?"([^"<]+)"',content)
			if pm:
				return pm.group(1)
		elif fmat == 'xml':
			pm = re.search('<{0}>([^<]+)</{0}>'.format(key), content)
			if not pm:
				pm = re.search(
					'<{0}><\!\[CDATA\[(.*?)\]\]></{0}>'.format(key), content)
			if pm:
				return pm.group(1)
		return '未知'
	def _transcoding(self,data):
		if not data:
			return data
		result = None
		if type(data) == unicode:
			result = data
		elif type(data) == str:
			result = data.decode('utf-8')
		return result
	def _xiaodoubi(self,word):
		url = 'http://www.xiaodoubi.com/bot/chat.php'
		print('这是小逗比')
		try:
			params = {'chat':word}
			r = self.myRequests.post(url,data=json.dumps(params))
			print(r.content)
			return r.content
		except:
			print("信号不好，收不到")
			return "信号不好，收不到"
			
	def _qingyunke(self,word):
		url = 'http://api.qingyunke.com/api.php'
		try:
			params = {'key':'free','appid':0,'msg':word}
			r = self.myRequests.post(url,params=params)
			r.encoding = 'utf-8'
			strmap = json.loads(r.content)
			print(strmap['content'])
			return strmap['content']
		except Exception as e:
			print(e)
			print("信号不好，收不到")
			return("信号不好，收不到")
			
	def _saveFile(self,filename,data,api=None):
		fn = filename
		if self.saveSubFolders[api]:
			dirName = os.path.join(self.saveFolder,self.saveSubFolders[api])
			if not os.path.exists(dirName):
				os.makedirs(dirName)
			fn = os.path.join(dirName,filename)
			with open(fn,'wb') as f:
				f.write(data)
				f.close()
		return fn
		
	def _safe_open(self,path):
		if self.autoOpen:
			if sys.platform.find('linux') >= 0:
				subprocess.call(['xdg-open',path])
			else:
				subprocess.call(['open',path])
				
	
	@catchKeyboardInterrupt
	def start(self):
		self._echo('[*] 微信网页版 ... 开动')
		self._run('正在获取uuid ...',self.getUUID)
		self._run('正在获取二维码',self.showQRImage)
		while self.waitForLogin() != '200':
			pass
		os.remove(self.QRImagePath)
		self._run('正在登陆 ... ',self.login)
		self._run('微信初始化 ...',self.webwinit)
		self._run('开启状态通知。。',self.webwxstatusnotify)
		self._run('获取联系人..',self.webwxgetcontact)
		self._echo('应有%s个联系人，读取到联系人 %d个'%(self.MemberCount,len(self.MemberList)))
		self._run('获取群....',self.webwxbatchgetcontact)
		if raw_input('[*] 是否开启自动回复模式(y/n): ') == 'y':
			self.autoReplyMode = True
			print '[*] 自动回复模式 ... 开启'
		listenProcess = multiprocessing.Process(target=self.listenMsgMode)
		listenProcess.start()
		while True:
			text = raw_input('')
			if text == 'quit':
				listenProcess.terminate()
				print('[*] 退出微信')
				exit()
				
class UnicodeStreamFilter:
	def __init__(self,target):
		self.target = target
		self.encoding = 'utf-8'
		self.errors = 'replace'
		self.encode_to = self.target.encoding
		
	def write(self,s):
		if type(s) == str:
			s = s.decode('utf-8')
		s = s.encode(self.encode_to,self.errors).decode(self.encode_to)
		self.target.write(s)
		
	def flush(self):
		self.target.flush()
		
if sys.stdout.encoding == 'cp936':
	pass
	#sys.stdout = UnicodeStreamFilter(sys.stdout)
if __name__ == '__main__':
	reload(sys)
	sys.setdefaultencoding('utf-8')
	webwx = WebWeiXin()
	webwx.start()