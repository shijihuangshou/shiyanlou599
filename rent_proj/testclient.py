#from multiprocessing import Queue
import socket
from multiprocessing import Process


def run_proc(sock):
	print('run_proc')
	while True:
		word = sock.recv(1024)
		if word:
			print(word.decode('utf-8'))

if __name__ == "__main__":
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	server_address = ("localhost", 8888)
	sock.connect(server_address)

	name = input("input your name")
	sock.send(name.encode('utf-8'))
	p = Process(target=run_proc,args=(sock,))
	p.start()
	while True:
		word = input()
		sock.send(word.encode('utf-8'))
		if word == '@quit':
			break
		
	
	p.terminate()
	sock.shutdown(socket.SHUT_RDWR)