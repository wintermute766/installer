#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import signal
import Tkinter
from Tkinter import *
import tkFont

import time
import threading
import random
import Queue
import os
import sys

#HOST1 = '192.168.1.2'
#HOST1 = '127.0.0.1'
HOST1 = '8.8.8.8'
#HOST2 = '192.168.1.3'
HOST2 = '127.0.0.1'
#HOST2 = '8.8.8.8'

PLATFORM = sys.platform
CWD = os.getcwd()
CATALOG = '/mnt/1'
NUM = '1'
FILESIZE = 102400
MAX_FILES = 3

class GuiPart:
    def __init__(self, master, queue, resumeCommand, pauseCommand, endCommand):
        self.queue = queue

        self.fail1 = 0
        self.fail2 = 0
          
        self.customFont1 = tkFont.Font(family='Arial', size=24)
        self.customFont2 = tkFont.Font(family='Arial', size=64)
        self.customFont3 = tkFont.Font(family='Arial', size=56)

        self.txt0 = StringVar()
        self.txt0.set('                                                                      ')
        self.txt1 = StringVar()
        self.txt1.set('   ')
        self.txt2 = StringVar()
        self.txt2.set(u'\u21C4')

        self.text1 = Tkinter.Message(master, textvariable = self.txt0, font = self.customFont1, width = 600)
        self.text1.grid(row = 0, columnspan = 3)
        Frame(height = 3, bd = 1).grid(row = 1, columnspan = 3)

        self.text2 = Tkinter.Message(master, textvariable = self.txt0, font = self.customFont1, width = 600)
        self.text2.grid(row = 2, columnspan = 3)
        Frame(height = 3, bd = 1).grid(row = 3, columnspan = 3)

        self.label3 = Tkinter.Label(text = '    ЦОД 1    ', font = self.customFont2, fg = 'white', bg = 'grey')
        self.label3.grid(row = 4, column = 0, sticky=W)

        self.label4 = Tkinter.Label(text = '   ЦОД 2    ', font = self.customFont2, fg = 'white', bg = 'grey')
        self.label4.grid(row = 4, column = 2, sticky=E)
        Frame(height = 25, bd = 1).grid(row = 5, columnspan = 3)

        self.text3 = Tkinter.Message(master, textvariable = self.txt1, font = self.customFont3)
        self.text3.grid(row = 4, column = 1)

        text = 'Старт'
        if PLATFORM == 'win64':
            text = text.decode('cp1251')   
        self.button1 = Tkinter.Button(master, text=text, command=resumeCommand)
        self.button1.grid(row = 6, column = 0, sticky=E)

        text = 'Стоп'
        if PLATFORM == 'win64':
            text = text.decode('cp1251')   
        self.button2 = Tkinter.Button(master, text=text, command=pauseCommand, state = DISABLED)
        self.button2.grid(row = 6, column = 1)

        text = 'Завершить'
        if PLATFORM == 'win64':
            text = text.decode('cp1251')   
        self.button3 = Tkinter.Button(master, text=text, command=endCommand)
        self.button3.grid(row = 6, column = 2, sticky=W)

    def processIncoming(self):
        txt = StringVar()
        while self.queue.qsize():
            try:
                msg = self.queue.get(0)
                if msg == 'pause':
                    self.label3.configure(bg = 'grey', fg = 'white')
                    self.label4.configure(bg = 'grey', fg = 'white')

                elif msg == 'fail1':
                    self.fail1 = 1
                    self.label3.configure(bg = 'red', fg = 'white')

                elif msg == 'alive1':
                    self.fail1 = 0
                    self.label3.configure(bg = 'green', fg = 'black')

                elif msg == 'fail2':
                    self.fail2 = 1
                    self.label4.configure(bg = 'red', fg = 'white')

                elif msg == 'alive2':
                    self.fail2 = 0
                    self.label4.configure(bg = 'green', fg = 'black')

                elif msg == 'clear1':
                    self.text1.configure(textvariable=self.txt0)

                elif msg == 'clear2':
                    self.text2.configure(textvariable=self.txt0)
                    self.text3.configure(textvariable=self.txt1)

                elif msg == 'repl' and not self.fail1 and not self.fail2:
                    message = 'Репликация данных завершена'
                    if PLATFORM == 'win64':
                        message = message.decode('cp1251')
                    txt.set(message)
                    self.text2.configure(textvariable=txt)
                    self.text3.configure(textvariable=self.txt2)

                elif 'file' in msg and (not self.fail1 or not self.fail2):
                    message = 'Файл "' + msg + '" загружен в каталог ' + NUM
                    if PLATFORM == 'win64':
                        message = message.decode('cp1251')
                    txt.set(message)
                    self.text1.configure(textvariable=txt)

                self.button2.configure(state = "normal")
           
            except Queue.Empty:
                pass

class ThreadedClient:

    def __init__(self, master):
        self.master = master
        self.queue = Queue.Queue()
        self.gui = GuiPart(master, self.queue, self.resume, self.pause, self.endApplication)
            
        self.running = 1

        self.can_run = threading.Event()
        self.can_run.clear()
        self.job_done = threading.Event()
        self.job_done.clear()

        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        self.thread2 = threading.Thread(target=self.workerThread2)
        self.thread2.start()

        self.periodicCall()

    def periodicCall(self):
        self.gui.processIncoming()
        if not self.running:
            sys.exit(1)
        self.master.after(200, self.periodicCall)

    def workerThread1(self):
        while self.running:
            self.can_run.wait()
            self.job_done.clear()

            if ping(HOST1):
                self.queue.put('alive1')
            else:
                self.queue.put('fail1')
            if ping(HOST2):
                self.queue.put('alive2')
            else:
                self.queue.put('fail2')

            self.job_done.set()
            time.sleep(.5)

    def workerThread2(self):
        counter = 1

        while self.running:
            self.can_run.wait()
            self.job_done.clear()

            time.sleep(1)

            filename = os.path.join(CATALOG, 'file' + str(counter))
            try:
                with open(filename, 'wb') as fout:
                    fout.write(os.urandom(FILESIZE))
            except IOError:
                self.job_done.set()
                continue

            self.queue.put('file' + str(counter))
            time.sleep(1 + random.random())
            self.queue.put('clear1')

            self.queue.put('repl')
            time.sleep(1 + random.random())
            self.queue.put('clear2')

            counter += 1

            if counter > MAX_FILES:
                filename = os.path.join(CATALOG, 'file' + str(counter-MAX_FILES))
                try:
                    os.remove(filename)
                except (IOError, OSError):
                    pass

            self.job_done.set()

            time.sleep(1)
 
    def pause(self):   
        self.can_run.clear()
        self.job_done.wait()
        time.sleep(2)
        self.queue.put('pause')

    def resume(self):
        self.can_run.set()

    def endApplication(self):
        self.can_run.set()
        self.running = 0

def ping(host):
    if PLATFORM == "win32" or PLATFORM == "win64":
        ping_str = "-n 1"
    else:
        ping_str = "-c 1"
    return os.system("ping " + ping_str + " -w 1 " + host) == 0

root = Tkinter.Tk()
root.geometry("1015x300")
root.title("Мониторинг ЦОД")

client = ThreadedClient(root)
root.mainloop()