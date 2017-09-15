from PIL import Image,ImageDraw,ImageFont
import argparse
import os

ascii_char = list("$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. ")

def get_char(r,b,g,alpha = 256):
	if alpha == 0:
		return ' '
	length = len(ascii_char)
	gray = int(0.2126*r + 0.7152*g + 0.0722*b)
	unit = (256.0+1)/length
	return ascii_char[int(gray/unit)]

#WIDTH = 200
#HEIGHT = 200
SIZE = 8
def imgtochar(img):
	im = Image.open(img)
	WIDTH,HEIGHT = im.size
	width = WIDTH/SIZE
	height = HEIGHT/SIZE
	im = im.resize((width,height),Image.NEAREST)
	names = img.split('.')
	newName = names[0] + 'ascii.' + names[1]
	a = Image.new('RGBA',(width*SIZE,height*SIZE),(0,0,0))
	dr = ImageDraw.Draw(a)
	#fnt = ImageFont.truetype('simsun.ttc',50)
	for i in range(height):
		for j in range(width):
			dr.text((j*SIZE,i*SIZE),get_char(*im.getpixel((j,i))))
	#a = a.resize((WIDTH,HEIGHT),Image.NEAREST)
	newName = os.path.join(os.getcwd(),newName)
	#print(newName)
	saveform = 'PNG'
	if names[1] == 'jpg':
		saveform = 'JPEG'
	print(saveform)
	a.save(newName,saveform)
	return newName
#imgtochar('ascii_dora.png')


def imgtohalf(img):
	im = Image.open(img)
	im2 = Image.open(img)
	WIDTH,HEIGHT = im.size
	width = WIDTH/SIZE
	height = HEIGHT/SIZE
	im = im.resize((width,height),Image.NEAREST)
	names = img.split('.')
	newName = names[0] + 'ascii.' + names[1]
	a = Image.new('RGBA',(WIDTH,HEIGHT),(0,0,0))
	dr = ImageDraw.Draw(a)
	#fnt = ImageFont.truetype('simsun.ttc',50)
	for i in range(HEIGHT):
		for j in range(WIDTH):
			if j % SIZE == 0 and i % SIZE == 0 and j < WIDTH//2:
				dr.text((j,i),get_char(*im2.getpixel((j,i))))
			elif j > WIDTH//2:
				a.putpixel((j,i),im2.getpixel((j,i)))
	#a = a.resize((WIDTH,HEIGHT),Image.NEAREST)
	newName = os.path.join(os.getcwd(),newName)
	#print(newName)
	saveform = 'PNG'
	if names[1] == 'jpg':
		saveform = 'JPEG'
	print(saveform)
	a.save(newName,saveform)
	return newName