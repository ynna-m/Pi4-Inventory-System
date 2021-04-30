from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import sys
from gui import Ui_MainWindow
from collections import OrderedDict

class Parent(QMainWindow, Ui_MainWindow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.flag_test = False
		self.objects = OrderedDict()
		print("objects:")
		print(bool(self.objects))
		self.thread = QThread()
		self.Child = Child(self)
		self.Child.moveToThread(self.thread)
		self.thread.started.connect(self.Child.run)
		self.thread.start()
		time.sleep(3)
		self.objects[0] = "lol"
		print("objects:")
		print(bool(self.objects))
		time.sleep(3)
		del self.objects[0]
		print("objects:")
		print(bool(self.objects))
		self.flag_test = True
		
class Child(QObject):
	def __init__(self,parent):
		# print(parent.flag_test)
		super().__init__()
		self.flag_test = parent.flag_test
		
	def run(self):
		print(self.flag_test)
		print("Sleeping Thread")
		time.sleep(8)
		print("Thread Awake")
		print(self.flag_test)

if __name__ == "__main__":
	App = QApplication(sys.argv)
	Window = Parent()
	Window.show()
	sys.exit(App.exec())