# -*- coding: utf-8 -*-
# Author Bruce Zhu 8/11/2017

import os
import re
import time
import sys
from ftplib import FTP
ip = '192.168.0.105'
port = 3721  #pay attention to if you are using python3, port must be int.
username = 'a'
pwd = 'a'
dataPath = 'autoSQA/data/'
musicPath = 'autoSQA/music/TheLastGoodbye.mp3'
btName = 'M5_26451082'

class FtpBT:
    def __init__(self, host='', user='', passwd='', cmd=''):
            ftp=FTP()
            ftp.connect(ip,port)
            ftp.login(username, pwd)

    def ftp_up(self, path, filename):
        try:
            #print ftp.dir() #display file detail under directory
            #print ftp.nlst()
            ftp.cwd(path)
            bufsize = 1024
            file_handler = open(filename,'rb')
            ftp.storbinary('STOR %s' % os.path.basename(filename),file_handler,bufsize)
            #ftp.set_debuglevel(0)
            file_handler.close()
            ftp.quit()
            #print "ftp up OK"
            return True
        except Exception as e:
            tym_print(e)
            tym_print("network problem!")
            sys.exit()
            return False

    def ftp_down(self, path, filename):
        try:
            ftp.cwd(path)
            bufsize = 1024
            file_handler = open(filename,'wb').write
            ftp.retrbinary('RETR %s' % os.path.basename(filename),file_handler,bufsize)
            ftp.set_debuglevel(0)
            #file_handler.close()
            ftp.quit()
            #print "ftp down OK"
            return True
        except:
            tym_print("network problem!")
            sys.exit()
            return False

    def readFile(self, filename):
        try:
            filePath = "%s/%s"%(os.getcwd(),filename)
            file = open(filePath)
            for line in file.readlines():
                return line
            file.close()
        except:
            tym_print("file %s does not exist!"%filename)
            return ""

        def writeFile(filename,str):
            filePath = "%s/%s"%(os.getcwd(),filename)
            file = open(filePath,'w')
            file.write(str)
            file.close

    def deleteFile(self, src):
        if os.path.exist(src):
            try:
                os.remove(src)
            except:
                tym_print('delete file %s failed'%src)
        else:
            tym_print('delete file %s does not exist!'%src)

    def cmd(self, str):
        tym_print_append()
        print('%s'%str,)
        writeFile('cmd.ini',str)
        for i in range(0,5): #try 5 times
            if ftp_up(dataPath,'cmd.ini'):
                break;
            else:
                return False

        for i in range(0,5): #try 5 times
            if ftp_down(dataPath,'return.ini'):
                break;
            else:
                return False

        #time.sleep(0.05)
        value = readFile('return.ini')

        if value=='1':
            print('[Success]')
            return True
        elif value=='0':
            print('[Success]')
            return False
        else:
            print('[Failed]')