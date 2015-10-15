import time
from ctypes import *
import threading
import numpy as np
import math

class clockMem:
	def __init__(self,N):
		self.N = N
		self.mem = [(long(0),long(0)]*self.N
		self.pos = 0
		self.sumx = long(0)
		self.sumy = long(0)
		self.sumxy = long(0)
		self.sumxx = long(0)
		
	def update(self,x,y):
		(x0,y0) = self.mem[self.pos]
		self.sumx += x-x0
		self.sumy += y-y0
		self.sumxx += x*x - x0*x0
		self.sumyx += y*x - y0*x0
		self.mem[self.pos]=(x,y)
		self.pos+=1
		if self.pos>=self.N:
			self.pos -= self.N
		
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
		self.cm = clockMem(N)
		
	def timePair(self):
		cpu0 = long(self.lib.getNow())
		sys = long(time.time()*1e9)
		cpu1 = long(self.lib.getNow())
		return sys,(cpu0+cpu1)/2		
	
	def log(self):
		while len(self.mem)>=self.N:
			del self.mem[0]
		(x,y) = self.timePair()
		self.mem.append((x,y))
		self.cm.update(y,x)
		
	def run(self):
		while len(self.mem)<self.N:
			time.sleep(0.0001)
			self.log()
		cnt = 0
		while self.Stop==0:
			time.sleep(0.1)
			if cnt<0:
				cnt = self.calcA()
			else:
				cnt -= 1	
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

	def calcA(self):
		if len(self.mem)==0:
			return
		(y0,x0)=self.mem[-1]
		(y1,x1)=self.mem[-2]
		cs = np.array([[float(y-y0),float(x-x0)] for (y,x) in self.mem])
		n = len(cs[:,0])
		ys = sum(cs[:,0])/n
		xs = sum(cs[:,1])/n
		cs = cs-[ys,xs]
		xxs = sum(cs[:,1]*cs[:,1])/n
		yxs = sum(cs[:,0]*cs[:,1])/n
		#A = np.matrix([[1.,xs],[xs,xxs]])
		#f = A.I*np.matrix([[ys],[yxs]])
		self.factor = long(yxs/xxs*(1<<48))
		self.offset = 0#long(ys*(1<<48))
		self.cpu0 = x0+long(xs)
		self.sys0 = y0+long(ys)
		self.ys = ys
		self.xs = xs
		self.xxs = xxs
		self.yxs = yxs
		#self.A = A
		f0 = yxs/xxs
		f1 = float(y1-y0)/float(x1-x0)
		cnt = 0.001/abs((math.log10(f0/f1)))
		if cnt>=1024:
			cnt = 1024
		print f0,f0/f1,cnt
		return int(cnt)
			
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
		time.sleep(1.5)
		print clk.factor,
		cpu0 = clk.Now()		
		now = time.time()*1e9
		cpu1 = clk.Now()
		print now-(cpu0+cpu1)/2
		#clk.calcA()
		#print clk.A,clk.xs,clk.ys,clk.xxs,clk.yxs,len(clk.mem)
	clk.Stop = 1
	time.sleep(1)
	print "Exit"
		
if __name__ == '__main__':
	main()
