#!/usr/bin/env python

import web
import sqlite3
import threading
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

def make_text(string):
    return string
 
urls = ('/', 'salesstatus')
render = web.template.render('templates/')
 
app = web.application(urls, globals())

class Repository(object):
	def __init__(self):
		self.conn = 'countdown.db'

	def get_current_count(self):
		db = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
		cursor = db.execute("""
			SELECT num_sales
			FROM tblCurrentCount
			WHERE id = 1;
		""")
		value = cursor.fetchall()[0][0]
		db.close()
		return value

	def increment_count(self,index):
		print('index to insert: ' + str(index))
		db = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
		db.execute('UPDATE tblCurrentCount SET num_sales = ' + str(index) + ' WHERE id = 1;')
		db.commit()
		db.close()
		return True

class Button(threading.Thread):
	"""A Thread that monitors a GPIO button"""

	def __init__(self, channel):
		threading.Thread.__init__(self)
		self._pressed = False
		self.channel = channel

		# set up pin as input
		GPIO.setup(self.channel, GPIO.IN)

		# terminate this thread when main program finishes
		self.daemon = True

		# start thread running
		self.start()

	def pressed(self):
		if self._pressed:
			# clear the pressed flag now we have detected it
			self._pressed = False
			return True
		else:
			return False

	def run(self):
		previous = None
		while 1:
			# read gpio channel
			current = GPIO.input(self.channel)
			time.sleep(0.01) # wait 10 ms

			# detect change from 1 to 0 (a button press)
			if current == False and previous == True:
				self._pressed = True

				# wait for flag to be cleared
				while self._pressed:
					time.sleep(0.05) # wait 50 ms

			previous = current

class ButtonMonitor(threading.Thread):
	def __init__(self, button):
		threading.Thread.__init__(self)
		self.button = button
		self.daemon = True

		repo = Repository()
		self.index = int(repo.get_current_count())

		self.start()

	def onButtonPress(self):
		repo = Repository()
		self.index -= 1
		if self.index < 0:
			print(str(self.index) + ': reset to 20')
			self.index = 20
			repo.increment_count(20)
		print(str(self.index))
		repo.increment_count(self.index)

	def run(self):
		while 1:
			if self.button.pressed():
				self.onButtonPress()

class salesstatus:
	def GET(self):
		repo = Repository()
		index = repo.get_current_count()
		imgAddr = "./static/%s.png" % str(index)
		return render.salesstatus(imgAddr)
		#return make_text("./static/" + str(index) + ".png")

	def POST(self):
		repo = Repository()
		index = repo.get_current_count()
		print("./static/" + str(index) + ".png")
		return make_text("./static/" + str(index) + ".png")

button = Button(11)
monitor = ButtonMonitor(button)

if __name__ == '__main__':
	app.run()
	print('started')