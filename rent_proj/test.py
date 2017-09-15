from queue import Queue
import socket

from functools import partial

from tornado.ioloop import IOLoop

class User():
	def __init__(self,fd,sock,cli_addr):
		self.fd = 0
		self.sock = sock
		self.cli_addr = cli_addr
		self.sendBlock = ''
		self.name = False
	def setName(self,name):
		self.name = name
	def getName(self):
		return self.name
	def putMessage(self,block):
		self.sendBlock = self.sendBlock + block
	def doWrite(self):
		num = self.sock.send(self.sendBlock.encode('utf-8'))
		if num > 0:
			self.sendBlock = self.sendBlock[num-1:]
		else:
			self.close()
	def close(self):
		self.sock.close()

class ChatRoom():
	def __init__(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setblocking(0)
		server_address = ("localhost", 8888)
		self.sock.bind(server_address)
		self.sock.listen(5)
		self.user_map = {} #所有的用户
		self.fd_map = {}
		self.ioloop = IOLoop.instance()
		self.fd = self.sock.fileno()
		self.fd_map[self.fd] = self.sock
	def start(self):
		self.ioloop.add_handler(self.fd, self.handle_event, IOLoop.READ)
		self.ioloop.start()
	def enterRoom(self,fd,sock,cli_addr):
		user = User(fd,sock,cli_addr)
		self.user_map[fd] = user
		self.fd_map[fd] = sock
		
	def removefd(self,fd):
		self.fd_map.pop(fd)
		self.user_map.pop(fd)
	def doSend(self):
		r = ''
		while True:
			fd = yield r
			if fd:
				user = self.user_map[fd]
				if user:
					user.doWrite()
	def broadcast(self,fd,message):
		print('broadcast %s'%message)
		c = self.doSend()
		c.send(None)
		for k in self.user_map:
			if k != fd:
				v = self.user_map[k]
				v.putMessage(message)
				c.send(k)
	def handle_event(self,fd, event):
		s = self.fd_map[fd]
		if event & IOLoop.READ:
			if fd == self.fd:
				conn, cli_addr = s.accept()
				print (" connection %s" % cli_addr[0])
				conn.setblocking(0)
				conn_fd = conn.fileno()
				self.enterRoom(conn_fd,conn,cli_addr)
				# 将连接和handle注册为读事件加入到 tornado ioloop
				self.ioloop.add_handler(conn_fd, self.handle_event, IOLoop.READ)
			else:
				data = s.recv(1024).decode('utf-8')
				user = self.user_map[fd]
				if data and user:
					if user.getName():
						if data == '@quit':
							message = user.getName() +"quit room \n"
							self.removefd(fd)
							self.ioloop.remove_handler(fd)
							s.close()
						else:
							message = user.getName() +" : "+data+"\n"
						print('handle_event %s'%message)
						self.broadcast(fd,message)
					else:
						user.setName(data)
						message = data +" enterRoom "
						self.broadcast(-1,message)
				else:
					self.removefd(fd)
					self.ioloop.remove_handler(fd)
					s.close()
					
		if event & IOLoop.ERROR:
			print (" exception on %s" % cli_addr)
			ioloop.remove_handler(fd)
			s.close()
			self.removefd(fd)
			
chatroom = ChatRoom()
chatroom.start()

