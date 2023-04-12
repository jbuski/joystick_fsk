#!/usr/bin/python
import pygame
import signal
import math
import sys,os
import curses
import time
import subprocess
import threading
import select



def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        curses.endwin()
        sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
#sys.stdout = os.devnull
#sys.stderr = os.devnull

screen = curses.initscr()
curses.noecho()
curses.curs_set(0)
pwi=0
pwi_f=0
pwi_s=0
auto_iris=0
auto_iris_f=0
auto_iris_s=0
class Receiver:
    def __init__(self, **kwargs):
        pass

class Transmitter:
    def __init__(self, **kwargs):
        arg= '-t -A1 '+'-pO '
        print(arg)        
        self.p = subprocess.Popen(['minimodem','-tA1', '-pO','-M2400','-S2640','200'
	   ] + kwargs.get('extra_args', []),
           stdin=subprocess.PIPE)
    def write(self, text):
        self.p.stdin.write(text)

    def close(self):
        self.p.stdin.close()
        self.p.wait()


class Receiver:
    class ReceiverReader(threading.Thread):
        def __init__(self, stdout, stderr):
            threading.Thread.__init__(self)
            self.stdout = stdout
            self.stderr = stderr
            self.packets = []

        def run(self):
            in_packet = False
            packet = ''
            while True:
                readers, _, _ = select.select([self.stdout, self.stderr], [], [])
                if in_packet:
                    if self.stdout in readers:
                        data = self.stdout.read(1)
                        if not data:
                            break
                        packet += data
                        continue
                if self.stderr in readers:
                    line = self.stderr.readline()
                    if not line:
                        break
                    if line.startswith('### CARRIER '):
                        in_packet = True
                        packet = ''
                    elif line.startswith('### NOCARRIER '):
                        in_packet = False
                        print 'Got packet: %s' % packet
                        self.packets.append(packet)

    def __init__(self, **kwargs):
        self.p = subprocess.Popen(['minimodem', '-r', '-8',
            kwargs.get('baudmode', 'rtty')] + kwargs.get('extra_args', []),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.reader = Receiver.ReceiverReader(self.p.stdout, self.p.stderr)
        self.reader.setDaemon(True)
        self.reader.start()



receiver = Receiver()
sender = Transmitter()
screen.keypad(1)

pygame.init() 
pygame.joystick.init() 
js = pygame.joystick.Joystick(0) 
js.init() 
buttons = js.get_numbuttons() 
axis = js.get_numaxes() 
balls = js.get_numballs()
hats = js.get_numhats()
#screen.addstr(0,0,"buttons: " + str(buttons)+" axis: " + str(axis) + " balls: " + str(balls) + " hats: " + str(hats))
while True:
    pygame.event.get()
    jx = js.get_axis(0)
    jy = js.get_axis(1)
    jz = js.get_axis(2)
    jz1 = js.get_axis(3)
    jb1 = js.get_button(0)
    jb2 = js.get_button(1)
    jb3 = js.get_button(2)
    jb4 = js.get_button(3)
    hat1 = js.get_hat(0)
    if jx<0:
	screen.addstr(0,0,"left  ")
	lr=1
    elif jx>0:
	screen.addstr(0,0,"right ")
	lr=2
    else:
	screen.addstr(0,0,"stop  ")
	lr=0
	lr_f=0	
    if jy<0:
        screen.addstr(0,6,"up    ")
	ud=1
    elif jy>0:
        screen.addstr(0,6,"down  ")
	ud=2
    else:
        screen.addstr(0,6,"stop  ")
	ud=0
	ud_f=0
   
    if (lr==1) and (ud==0) and (lr_f==0):
	sender.write("\0x83\x41")
	screen.addstr(0,18,"0x41")	
	time.sleep(0.2)
	lr_f=1
    if (lr==2) and (ud==0) and (lr_f==0):
        sender.write("\0x83\x42")
        screen.addstr(0,18,"0x42")
        time.sleep(0.2)
        lr_f=1
    if (lr==0) and (ud==1) and (ud_f==0):
        sender.write("\0x83\x44")
        screen.addstr(0,18,"0x44")
        time.sleep(0.2)
        ud_f=1
    if (lr==0) and (ud==2) and (ud_f==0):
        sender.write("\0x83\x48")
        screen.addstr(0,18,"0x48")
        time.sleep(0.2)
        ud_f=1
 
    if (lr!=0) or (ud!=0): 
    	sender.write("\xFF")
	screen.addstr(0,12,"0xFF  ")
	time.sleep(0.1)
    else:
	sender.write("\x83\x40\x00")
	screen.addstr(0,12,"0x00  ")
    	time.sleep(0.2)
    if (hat1[1]>0):
	screen.addstr(0,24,"zoom in   ")
    elif (hat1[1]<0):
	screen.addstr(0,24,"zoom out  ")
    else:
        screen.addstr(0,24,"zoom stop ")
    if (hat1[0]>0):
        screen.addstr(0,36,"focus far   ")
    elif (hat1[0]<0):
        screen.addstr(0,36,"focus near  ")
    else:
        screen.addstr(0,36,"focus stop  ")
    if (jb1==1):
        if (pwi_f==0):
		pwi= not pwi
		pwi_s=1
	pwi_f=1
    else:
        pwi_f=0
    if (pwi_s==1):
	    pwi_s=0
	    if (pwi==1):
		screen.addstr(0,50,"pwi on  ")
	    else:
        	screen.addstr(0,50,"pwi off ")
    if (jb4==1):
	screen.addstr(0,60,"open  iris      ")
	auto_iris=0
    elif (jb3==1):
        screen.addstr(0,60,"close  iris     ")
	auto_iris=0
    else:
	if (auto_iris==0):
		screen.addstr(0,60,"stop   iris     ")
    if (jb2==1):
        if (auto_iris_f==0):
                if (auto_iris==0):
			auto_iris=1
		elif (auto_iris==1):
			auto_iris=2
		elif (auto_iris==2):
			auto_iris=1
                auto_iris_s=1
        auto_iris_f=1
    else:
        auto_iris_f=0
    if (auto_iris_s==1):
            auto_iris_s=0
            if (auto_iris==1):
                screen.addstr(0,60,"auto  iris peak ")
            elif (auto_iris==2):
                screen.addstr(0,60,"auto  iris aver ")
    #screen.addstr(0,0,"buttons: " + str(buttons)+" axis: " + str(axis))
    screen.addstr(1,0,"axis 0: " +str(jx) + " axis 1: " +str(jy) + " axis 2: " +str(jz) + " axis 3: " +str(jz1) + "   ")
    screen.addstr(2,0,"button 0: " +str(jb1) + " button 1: " +str(jb2) + " button 2: " +str(jb3)+ " button 3: " +str(jb4)+ "   ")	
    screen.addstr(3,0,"hats 0: " + str(hat1))
    #print('axis 0: ' + str(jx)+'axis 1:' + str(jy))
    #print('axis 0: ' + str(buttons)+'axis 1:' + str(axis))
    screen.refresh()
#curses.endwin()
