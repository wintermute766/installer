#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Tkinter import *

import time
import threading
import Queue
import os
import sys
import paramiko

class GuiPart:
   def __init__(self, master, queue, connect, install, endCommand):

      self.queue = queue

      fieldsDouble = (('Диски ПО СХД:', 'iso'),
            ('Параметры TFTP:', 'tftp'),
            ('Сервер EMS:', 'ems'),
            ('Серверы хранения:', 'gssio'))

      fieldsSingle = (('Имя кластера', 'cluster'),
            ('IP-адрес EMS:', 'ems_ip'),
            ('Логин:', 'login'),
            ('Пароль:', 'password'))

      entries = []

      self.txt0 = StringVar()
      self.txt0.set('   ')

      for field in fieldsDouble:
         self.row = Frame(master)
         self.lab = Label(self.row, width=20, text=field[0], anchor='w')
         self.ent = Text(self.row, height=3, width=70)
         self.row.pack(side=TOP, fill=X, padx=5, pady=5)
         self.lab.pack(side=LEFT)
         self.ent.pack(side=RIGHT, expand=YES, fill=X)
         entries.append((field[1], self.ent))

      for field in fieldsSingle:
         self.row = Frame(master)
         self.lab = Label(self.row, width=20, text=field[0], anchor='w')
         self.ent = Text(self.row, height=1, width=30)
         self.row.pack(side=TOP, fill=X, padx=5, pady=5)
         self.lab.pack(side=LEFT)
         self.ent.pack(side=LEFT, expand=NO)
         entries.append((field[1], self.ent))

      self.b1 = Button(master, text='Соединиться',
            command=(lambda e=entries: connect(e)))
      self.b1.pack(side=LEFT, padx=5, pady=5)

      self.b2 = Button(master, text='Начать установку',
            command=(lambda: install()), state = DISABLED)
      self.b2.pack(side=LEFT, padx=5, pady=5)

      self.b3 = Button(master, text='Выход', command=endCommand)
      self.b3.pack(side=RIGHT, padx=5, pady=5)

      self.lab0 = Label(textvariable=self.txt0)
      self.lab0.pack(side=LEFT)

      self.inst_window = object()
      self.msg0 = StringVar()
      self.inst_text = ''

   def processIncoming(self, master):
      while self.queue.qsize():
         try:
            msg = self.queue.get(0)
            if msg == 'msg_conn':
               self.b2.configure(state = "normal")
               self.txt0.set('Соединение установлено')
               self.lab0.configure(textvariable=self.txt0, fg = 'green')
            elif msg == 'msg_conn_error':
               self.b2.configure(state = DISABLED)
               self.txt0.set('Ошибка соединения')
               self.lab0.configure(textvariable=self.txt0, fg = 'red')
            elif msg == 'msg_inst':
               self.inst_window = new_window(master)
            else:
               self.inst_text += msg
               self.msg0.set(self.inst_text)
               self.inst_window.lab.configure(textvariable=self.msg0)
               
         except Queue.Empty:
            pass

class new_window:
   def __init__(self, master):
      self.master = master
      self.window0 = Toplevel(master)
      self.window0.title('Установка')
      self.lab = Label(self.window0, textvariable=StringVar())
      self.lab.pack(side=LEFT, expand=YES, padx=10, pady=10)

class app:

   def __init__(self, master):
      self.master = master
      self.queue = Queue.Queue()
      self.gui = GuiPart(master, self.queue, self.connect, self.install, self.endApplication)           
      self.running = 1

      self.client = paramiko.SSHClient()
      self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

      #self.thread1 = threading.Thread(target=self.workerThread1)
      #self.flag = 1

      self.periodicCall()

   def periodicCall(self):
      self.gui.processIncoming(self.master)
      if not self.running:
         sys.exit(1)
      self.master.after(200, self.periodicCall)

   def workerThread1(self):
      while self.running:
         chan = self.client.get_transport().open_session()
         chan.settimeout(10800)
         try:
             chan.exec_command('ls -la /home/eugene')
             while not chan.exit_status_ready():
                 if chan.recv_ready():
                     data = chan.recv(1024)
                     while data:
                         self.queue.put(data)
                         data = chan.recv(1024)
                         time.sleep(.2)

         except Exception:
            pass

   def connect(self, entries):
      ip = ''
      login = ''
      passw = ''
      for entry in entries:
         field = entry[0]
         #field = field.decode('utf-8')
         text  = entry[1].get('1.0', END)
         #text  = text.decode('utf-8')
         #print('%s "%s"' % (field, text.rstrip('\n')))
         if field == 'ems_ip':
            ip = text.rstrip('\n')
         if field == 'login':
            login = text.rstrip('\n')
         if field == 'password':
            passw = text.rstrip('\n')

      try:
         self.client.connect(ip, username=login, password=passw)
         self.queue.put('msg_conn')
      except Exception:
         self.queue.put('msg_conn_error')

   def install(self):
      self.queue.put('msg_inst')
      chan = self.client.get_transport().open_session()
      chan.settimeout(10800)
      try:
          chan.exec_command('ls -la ./')
          while not chan.exit_status_ready():
              if chan.recv_ready():
                  data = chan.recv(1024)
                  while data:
                      self.queue.put(data)
                      data = chan.recv(1024)

      except Exception:
         pass
      #if self.flag:
      #   self.thread1.start()
      #   self.flag = 0

   def endApplication(self):
      self.client.close()
      self.running = 0

if __name__ == '__main__':
   root = Tk()
   root.title("Установка ПО СХД")
   #root.bind('<Return>', (lambda event, e=ents: fetch(e)))
   client = app(root)
   root.mainloop()

#KEYBOARD INTERRUPT
#GIT