import time
from ctypes import *
import threading
import numpy as np

class clockCap:
	def __init__(self,N):
		self.lib=CDLL('./clock.so')
		self.lib.getNow.restype = c_long
		self.mem = []
		self.Stop = 0
		self.N = N
		self.factor = 1<<48
		self.offset = 0
		self.sys0, self.cpu0 = self.timePair()

	def timePair(self):
		cpu0 = long(self.lib.getNow())
		sys = long(time.time()*1e9)
		cpu1 = long(self.lib.getNow())
		return sys,(cpu0+cpu1)/2		
	
	def log(self):
		while len(self.mem)>=self.N:
			del self.mem[0]
		self.mem.append(self.timePair())
		
	def run(self):
		while len(self.mem)<self.N:
			#time.sleep(0.0001)
			self.log()
		while self.Stop==0:
			time.sleep(0.1)
			self.log()
		print "Thread Exit"
	
	def calc(self):
		if len(self.mem)==0:
			return
		(y0,x0)=self.mem[-1]
		cs = np.array([[float(y-y0),float(x-x0)] for (y,x) in self.mem])
		n = len(cs[:,0])
		ys = sum(cs[:,0])/n
		xs = sum(cs[:,1])/n
		xxs = sum(cs[:,1]*cs[:,1])/n
		yxs = sum(cs[:,0]*cs[:,1])/n
		A = np.matrix([[1.,xs],[xs,xxs]])
		f = A.I*np.matrix([[ys],[yxs]])
		self.factor = long(f[1,0]*(1<<48))
		self.offset = long(f[0,0]*(1<<48))
		self.cpu0 = x0
		self.sys0 = y0
		self.ys = ys
		self.xs = xs
		self.xxs = xxs
		self.yxs = yxs
		self.A = A
	
	def Now(self):
		cpu = self.lib.getNow()
		r = cpu-self.cpu0
		r *=int(self.factor)
		r +=self.offset
		r>>=48
		r+=self.sys0
		return r
		
def main():
	clk = clockCap(1024)
	t = threading.Thread(target=clk.run)
	t.start()
	for i in range(600):
		time.sleep(1)
		print clk.factor,
		cpu0 = clk.Now()		
		now = time.time()*1e9
		cpu1 = clk.Now()
		print now-(cpu0+cpu1)/2
		clk.calc()
		#print clk.A,clk.xs,clk.ys,clk.xxs,clk.yxs,len(clk.mem)
	clk.Stop = 1
	time.sleep(1)
	print "Exit"
		
if __name__ == '__main__':
	main()
