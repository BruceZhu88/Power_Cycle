# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        checkUpdates
# Purpose:
#
# Author:      Bruce Zhu
#
# Created:     8/11/2017
# Copyright:   (c) it 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

#cmd('disconnect bluetooth(%s)'%btName)
#cmd('connect bluetooth(%s)'%btName)
#cmd('bluetooth status()')
#cmd('PlayAudio(%s)'%musicPath)
#cmd('mediaVolumeUp()')
#cmd('mediaVolumeUp()')
#cmd('StopAudio()')

import os
import re
import time
import sys
import logging
from ftplib import FTP

class FtpBT:
    def __init__(self, host='', port=21, user='', passwd='', btName='', dataPath=''):
        self.ftp = FTP()
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.btName = btName
        self.dataPath = dataPath
        self.filePath = "%s\\UI\\data\\"%os.getcwd()

    def connect(self):
        try:
            self.ftp.connect(self.host, self.port)
            self.ftp.login(self.user, self.passwd)
            #print('Ftp connected!')
            return True
        except Exception as e:
            logging.log(logging.DEBUG, "Error when connecting FTP server: {0}".format(e))
            return False
            #sys.exit()

    def ftp_up(self, path, filename):
        try:
            #print ftp.dir() #display file detail under directory
            #print ftp.nlst()
            if not self.connect():
                return False
            self.ftp.cwd(path)
            bufsize = 1024
            file_handler = open(filename,'rb')
            self.ftp.storbinary('STOR %s' % os.path.basename(filename),file_handler,bufsize)
            #ftp.set_debuglevel(0)
            file_handler.close()
            self.ftp.quit()
            #print "ftp up OK"
            return True
        except Exception as e:
            logging.log(logging.DEBUG, "Error when ftp_up: {0}".format(e))
            #sys.exit()
            return False

    def ftp_down(self, path, filename):
        try:
            if not self.connect():
                return False
            self.ftp.cwd(path)
            bufsize = 1024
            file_handler = open(filename,'wb').write
            self.ftp.retrbinary('RETR %s' % os.path.basename(filename),file_handler,bufsize)
            self.ftp.set_debuglevel(0)
            #file_handler.close()
            self.ftp.quit()
            #print "ftp down OK"
            return True
        except Exception as e:
            logging.log(logging.DEBUG, "Error when ftp_down: {0}".format(e))
            #sys.exit()
            return False

    def readFile(self, filename):
        try:
            filePath = self.filePath + filename
            file = open(filePath)
            for line in file.readlines():
                return line
            file.close()
        except Exception as e:
            logging.log(logging.DEBUG, "File {0} does not exist: {1}".format(filename, e))
            return ""

    def writeFile(self, filename, s):
        filePath = self.filePath + filename
        file = open(filePath,'w')
        file.write(s)
        file.close

    def deleteFile(self, src):
        if os.path.exist(src):
            try:
                os.remove(src)
            except Exception as e:
                logging.log(logging.DEBUG, "Delete file {0} failed: {1}".format(src, e))
                #print('delete file %s failed'%src)
        else:
            logging.log(logging.DEBUG, "Delete file {0} does not exist!!".format(src))
            #print('delete file %s does not exist!'%src)

    def cmd(self, str):
        #print('%s'%str,)
        self.writeFile('cmd.ini',str)
        for i in range(0,5): #try 5 times
            if self.ftp_up(self.dataPath, self.filePath+'cmd.ini'):
                break;
            else:
                return False
        for i in range(0,5): #try 5 times
            if self.ftp_down(self.dataPath, self.filePath+'return.ini'):
                break;
            else:
                return False
        #time.sleep(0.05)
        value = self.readFile('return.ini')
        if value=='1':
            #print('[Success]')
            return '1'
        elif value=='0':
            #print('[Success]')
            return '0'
        else:
            #print('[Failed]')
            return False

if __name__ == '__main__':
    ip = '192.168.0.105'
    port = 3721  #pay attention to if you are using python3, port must be int.
    musicPath = 'autoSQA/music/TheLastGoodbye.mp3'
    btCmd = FtpBT(host=ip, port=port, user='', passwd='', btName='M5_26451082', dataPath='autoSQA/data/')
    status = btCmd.cmd('bluetooth status()')
    print(status)