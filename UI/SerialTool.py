# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        SerialTool
# Purpose:
#
# Author:      Bruce Zhu
#
# Created:     10/2016
# Copyright:   (c) it 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

import logging
import threading
import configparser
import _thread
import subprocess

from .Settings import Settings
from .PyTkinter import *
from .COM import FtpBT
from .COM import checkUpdates
#from .COM import logger
from tkinter.filedialog import *
from time import *
from .COM import SerialHelper
from serial.tools import list_ports

if not os.path.exists('./log'):
    os.mkdir('./log')
currentTime = strftime("%Y%m%d%H%M")
logging.basicConfig(filename='./log/{0}.log'.format(currentTime),
            format='%(asctime)s -%(name)s-%(levelname)s-%(module)s:%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S %p',
            level=logging.DEBUG)

monaco_font = ('Monaco', 12)
font = monaco_font
size_dict = dict()
size_dict = {
                "list_box_height": 19,
                "send_text_height": 12,
                "receive_text_height": 15,
                "reset_label_width": 24,
                "clear_label_width": 22
            }

conf = configparser.ConfigParser()
try:
    conf.read('./UI/version.ini')
    appVerson = conf.get("version", "app")
except Exception as e:
    logging.log(logging.DEBUG, 'Error: {0}'.format(e))
    sys.exit()

class SerialToolUI(object):
    def __init__(self):

        self.root = tk.Tk()
        self.create_frame()
        self.app_version = "SQA Power Cycle Tool v{0}".format(appVerson)
        self.portselect = None
        self.ser = None
        self.receive_count = 0
        self.count_pause = 0
        self.list_box_serial = list()
        self.find_all_serial() #thread 1
        self.runflag = False
        self.portDisconnect = False

        self.__settings = Settings('settings.joson')
        self.__firstLogIdx = 0
        self.__lastLogIdx = 0
        self.__lastSavedLogIdx = 0
        self.__autoSave = False
        self.__autoSavePath = None

        self.__autoSaveTimer = None

        self.create_frame()
        self.powerCycleID = 0
        #self.power_cycle_thread() #thread2

        self.host = None
        self.port = None
        self.user = None
        self.passwd = None
        self.btName = None
        self.dataPath = None
        self.checkBT = None
        self.time_press_button_power_on = None
        self.time_press_button_power_off = None
        self.ini_filename = '.\\Power_cycle.ini'

        self.menu_bar = None

    def mainLoop(self):
        self.__setupRoot()
        self.root.mainloop()

    def __setupRoot(self):
        # setup root
        if g_default_theme == "dark":
            self.root.configure(bg="#292929")
            combostyle = ttk.Style()
            combostyle.theme_use('alt')
            combostyle.configure("TCombobox", selectbackground="#292929", fieldbackground="#292929",
                                              background="#292929", foreground="#FFFFFF")
        self.root.resizable(False, False)
        self.root.title(self.app_version)
        self.root.iconbitmap("%s\\UI\\icon\\Power_48px.ico"%os.getcwd())

    def create_frame(self):
        '''
        Create new window, divide it into two parts, bottom part is state column
        '''
        self.menu_bar = Frame(self.root, relief=RAISED, borderwidth=2)
        self.frm = PyLabelFrame(self.root)
        self.frm_status = PyLabelFrame(self.root)

        self.menu_bar.grid(row=0, column=0, padx=0, pady=0, sticky="we")
        self.frm.grid(row=1, column=0, sticky="wesn")
        self.frm_status.grid(row=2, column=0, sticky="wesn")

        help_menu = self.create_help_menu()
        #about_menu = self.create_about_menu()
        tools_menu = self.create_tools_menu()
        self.menu_bar.tk_menuBar(help_menu, tools_menu)
        self.create_frm()
        self.create_frm_status()

    def create_help_menu(self):
        HELP_MENU_ITEMS = ['Undo', 'How to use', 'About']
        help_item = Menubutton(self.menu_bar, text='Help', underline=1)
        help_item.pack(side=LEFT, padx='1m')
        help_item.menu = Menu(help_item)

        help_item.menu.add('command', label=HELP_MENU_ITEMS[0])
        help_item.menu.entryconfig(1, state=DISABLED)

        help_item.menu.add_command(label=HELP_MENU_ITEMS[1])
        help_item.menu.add_command(label=HELP_MENU_ITEMS[2], command=self.about)
        help_item['menu'] = help_item.menu
        return help_item

    def create_tools_menu(self):
        TOOLS_MENU_ITEMS = ['Check for Updates']
        tools_item = Menubutton(self.menu_bar, text='Tools', underline=1)
        tools_item.pack(side=LEFT, padx='1m')
        tools_item.menu = Menu(tools_item)
        tools_item.menu.add_command(label=TOOLS_MENU_ITEMS[0], command=self.checkForUpdates)
        tools_item['menu'] = tools_item.menu
        return tools_item

    def about(self):
        messagebox.showinfo('About', 'Versoin: {0}\nAuthor: Bruce Zhu\nEmail: bruce.zhu@tymphany.com'.format(appVerson))

    def checkForUpdates(self):
        conf = configparser.ConfigParser()
        try:
            conf.read('.\\UI\\version.ini')
            currentVer = conf.get("version", "app")
        except Exception as e:
            logging.log(logging.DEBUG, 'Error: {0}'.format(e))
            return
        if not os.path.exists('.\\download'):
            os.makedirs('.\\download')
        dest_dir = '.\\download\\downVer.ini'
        checkupdates = checkUpdates()
        if not checkupdates.downLoadFromURL('http://sw.tymphany.com/fwupdate/sqa/tool/PowerCycle/version.ini', dest_dir):
            messagebox.showinfo('Tips', 'Cannot communicate with new version server!\nPlease check your network!')
            return
        downVer = checkupdates.getVer(dest_dir)
        logging.log(logging.DEBUG, 'Starting compare version')
        if checkupdates.compareVer(downVer, currentVer):
            ask = messagebox.askokcancel('Tips', 'New version %s is detected !\n Do you want to update now?'%downVer)
            if ask:
                self.downloadThread(downVer)
                logging.log(logging.DEBUG, 'Starting download')
        else:
            messagebox.showinfo('Tips', 'No new version!')

    def downloadThread(self, downVer):
        try:
            _thread.start_new_thread(self.downloadZip, (downVer,) )
        except:
            logging.log(logging.DEBUG, 'Cannot start power cycle thread!!!')

    def downloadZip(self, downVer):
        newVerPath = '.\\download\\PowerCycle.zip'
        installFile = '.\\download\\install.bat'
        checkupdates = checkUpdates()
        if not checkupdates.downLoadFromURL('http://sw.tymphany.com/fwupdate/sqa/tool/PowerCycle/PowerCycle_v{0}.zip'.format(downVer), newVerPath):
            messagebox.showinfo('Tips', 'Cannot communicate with new version server!\nPlease check your network!')
            return
        if not checkupdates.downLoadFromURL('http://sw.tymphany.com/fwupdate/sqa/tool/PowerCycle/install.bat', installFile):
            messagebox.showinfo('Tips', 'Cannot communicate with new version server!\nPlease check your network!')
            return
        #download process
        checkupdates.unzip_dir(newVerPath, '.\\download\\PowerCycle')
        ask = messagebox.askokcancel('Tips', 'Do you want to install this new version?')
        if ask:
            logging.log(logging.DEBUG, "Starting install")
            self.installThread()
            logging.log(logging.DEBUG, "Close UI")
            self.root.destroy()
            logging.log(logging.DEBUG, "System exit")
            sys.exit()

    def installThread(self):
        batPath = r'"%s\\download\\install.bat"'%os.getcwd() #Note: path must be '"D:\Program Files"' to avoid include space in path
        logging.log(logging.DEBUG, "Run %s"%batPath)
        try:
            _thread.start_new_thread(self.execBat, (batPath,) )
        except Exception as e:
           logging.log(logging.DEBUG, 'Error when install: {0}'.format(e))

    def execBat(self, path):
        os.system(path)
        #subprocess.Popen(Path, shell=True, stdout=subprocess.PIPE)

    def create_frm(self):
        '''
        Top part divided into left and right part
        '''
        self.frm_left = PyLabelFrame(self.frm)
        self.frm_right = PyLabelFrame(self.frm)

        self.frm_left.grid(row=0, column=0, padx=5, pady=5, sticky="wesn")
        self.frm_right.grid(row=0, column=1, padx=5, pady=5, sticky="wesn")

        self.create_frm_left()
        self.create_frm_right()

    def create_frm_left(self):
        '''
        Top part left window:
        Listbox--> display usable COM port
        Button--> connect device
        '''
        self.frm_left_label = PyLabel(self.frm_left,
                                           text="Serial Ports",
                                           font=font)
        self.frm_left_listbox = PyListbox(self.frm_left,
                                               height=size_dict["list_box_height"],
                                               font=font)
        self.frm_left_serial_set = PyLabelFrame(self.frm_left)
        self.frm_left_open_btn = PyButton(self.frm_left,
                                          text="Open",
                                          font=font,
                                          state='disabled',
                                          command=self.Toggle)

        self.frm_left_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.frm_left_listbox.grid(row=1, column=0, padx=5, pady=5, sticky="wesn")
        self.frm_left_serial_set.grid(row=2, column=0, padx=5, pady=5, sticky="wesn")
        self.frm_left_open_btn.grid(row=3, column=0, padx=5, pady=5, sticky="wesn")

        self.frm_left_listbox.bind("<Double-Button-1>", self.Double_click)
        self.create_frm_left_serial_set()


    def create_frm_left_serial_set(self):
        setting_label_list = ["BaudRate :", "Parity :", "DataBit :", "StopBit :"]
        baudrate_list = ["1200", "2400", "4800", "9600", "14400", "19200", "38400",
                         "43000", "57600", "76800", "115200", "12800"]
        # PARITY_NONE, PARITY_EVEN, PARITY_ODD PARITY_MARK, PARITY_SPACE
        parity_list = ["N", "E", "O", "M", "S"]
        bytesize_list = ["5", "6", "7", "8"]
        stopbits_list = ["1", "1.5", "2"]
        for index,item in enumerate(setting_label_list):
            frm_left_label_temp = PyLabel(self.frm_left_serial_set,
                                               text=item,
                                               font=('Monaco', 10))
            frm_left_label_temp.grid(row=index, column=0, padx=1, pady=2, sticky="e")
        self.frm_left_combobox_baudrate = ttk.Combobox(self.frm_left_serial_set,
                                                       width=15,
                                                       values=baudrate_list)
        self.frm_left_combobox_parity = ttk.Combobox(self.frm_left_serial_set,
                                                       width=15,
                                                       values=parity_list)
        self.frm_left_combobox_databit = ttk.Combobox(self.frm_left_serial_set,
                                                       width=15,
                                                       values=bytesize_list)
        self.frm_left_combobox_stopbit = ttk.Combobox(self.frm_left_serial_set,
                                                       width=15,
                                                       values=stopbits_list)
        self.frm_left_combobox_baudrate.grid(row=0, column=1, padx=2, pady=2, sticky="e")
        self.frm_left_combobox_parity.grid(row=1, column=1, padx=2, pady=2, sticky="e")
        self.frm_left_combobox_databit.grid(row=2, column=1, padx=2, pady=2, sticky="e")
        self.frm_left_combobox_stopbit.grid(row=3, column=1, padx=2, pady=2, sticky="e")

        self.frm_left_combobox_baudrate.current(3)
        self.frm_left_combobox_parity.current(0)
        self.frm_left_combobox_databit.current(3)
        self.frm_left_combobox_stopbit.current(0)

    def create_frm_right(self):
        '''
        '''
        self.frm_right_setting = PyLabelFrame(self.frm_right)

        self.frm_right_data_set = PyLabelFrame(self.frm_right)

        self.frm_right_savepath = PyLabelFrame(self.frm_right)

        self.frm_right_clear = PyLabelFrame(self.frm_right)

        self.frm_right_print = PyScrolledText(self.frm_right,
                                             width=50,
                                             height=size_dict["receive_text_height"],
                                             font=("Monaco", 9))


        self.frm_right_setting.grid(row=0, column=0, padx=1, sticky="wesn")
        self.frm_right_data_set.grid(row=1, column=0, padx=1, sticky="wesn")
        self.frm_right_savepath.grid(row=2, column=0, padx=1, sticky="wesn")
        self.frm_right_clear.grid(row=3, column=0, padx=1, sticky="wesn")
        self.frm_right_print.grid(row=4, column=0, padx=1, sticky="wesn")

        self.frm_right_print.tag_config("green", foreground="#228B22")

        self.create_frm_right_setting()
        self.create_frm_right_data_set()
        self.create_frm_right_savepath()
        self.create_frm_right_clear()

    def create_frm_right_setting(self):
        self.frm_right_setting_label = PyLabel(self.frm_right_setting,
                                                  text="Settings" + " "*size_dict["reset_label_width"],
                                                  font=font)

        self.frm_right_run_btn = PyButton(self.frm_right_setting,
                                                text="Run",
                                                width=10,
                                                font=font,
                                                command=self.Run)

        self.frm_right_clearSettings_btn = PyButton(self.frm_right_setting,
                                                text="Empty",
                                                width=10,
                                                font=font,
                                                command=self.ClearSettingsbtn)

        self.frm_right_setting_label.grid(row=0, column=0, sticky="w")
        self.frm_right_run_btn.grid(row=0, column=1, padx=5, pady=5, sticky="wesn")
        self.frm_right_clearSettings_btn.grid(row=0, column=2, padx=5, pady=5, sticky="wesn")

    def create_frm_right_data_set(self):
        self.frm_right_count_label = PyLabel(self.frm_right_data_set,
                                                  text="Total Count" + " "*size_dict["reset_label_width"],
                                                  font=font)

        self.countStr = tk.StringVar()
        self.frm_right_count_entry = PyEntry(self.frm_right_data_set,
                                                      textvariable=self.countStr,
                                                      width=6,
                                                      font=font)


        self.frm_right_timeon_label = PyLabel(self.frm_right_data_set,
                                                  text="Time ON(s)" + " "*size_dict["reset_label_width"],
                                                  font=font)

        self.timeonStr = tk.StringVar()
        self.frm_right_timeon_entry = PyEntry(self.frm_right_data_set,
                                                      textvariable=self.timeonStr,
                                                      width=6,
                                                      font=font)

        self.frm_right_timeoff_label = PyLabel(self.frm_right_data_set,
                                                  text="Time OFF(s)" + " "*size_dict["reset_label_width"],
                                                  font=font)

        self.timeoffStr = tk.StringVar()
        self.frm_right_timeoff_entry = PyEntry(self.frm_right_data_set,
                                                      textvariable=self.timeoffStr,
                                                      width=6,
                                                      font=font)

        self.frm_right_label_purpose = PyLabel(self.frm_right_data_set,
                                                  text="Purpose(AC/Button)" + " "*size_dict["reset_label_width"],
                                                  font=font)
        purpose_set = ['AC', 'Button']
        self.frm_right_combobox_purpose = ttk.Combobox(self.frm_right_data_set,
                                                       width=15,
                                                       values=purpose_set)

        self.frm_right_label_port = PyLabel(self.frm_right_data_set,
                                                  text="Port Address" + " "*size_dict["reset_label_width"],
                                                  font=font)

        port = ['01', '02', '04', '08', '10', '20', '40', '80']
        self.frm_right_combobox_port = ttk.Combobox(self.frm_right_data_set,
                                                       width=15,
                                                       values=port)

        self.frm_right_count_label.grid(row=0, column=0, padx=5, pady=5)
        self.frm_right_count_entry.grid(row=0, column=1, padx=5, pady=5)
        self.frm_right_timeon_label.grid(row=1, column=0, padx=5, pady=5)
        self.frm_right_timeon_entry.grid(row=1, column=1, padx=5, pady=5)
        self.frm_right_timeoff_label.grid(row=2, column=0, padx=5, pady=5)
        self.frm_right_timeoff_entry.grid(row=2, column=1, padx=5, pady=5)
        self.frm_right_label_purpose.grid(row=3, column=0, padx=5, pady=5)
        self.frm_right_combobox_purpose.grid(row=3, column=1, padx=5, pady=5)
        self.frm_right_label_port.grid(row=4, column=0, padx=5, pady=5)
        self.frm_right_combobox_port.grid(row=4, column=1, padx=5, pady=5)

        self.frm_right_combobox_purpose.current(0)
        self.frm_right_combobox_port.current(0)

    def create_frm_right_savepath(self):
        self.frm_right_savepath_label = PyLabel(self.frm_right_savepath,
                                                  text=''+ " "*size_dict["clear_label_width"],
                                                  font=font)

        #self.frm_right_savepath_label.grid(row=0, column=0, padx=5, pady=5, sticky="wesn")

    def create_frm_right_clear(self):
        self.receive_hex_cbtn_var = tk.IntVar()
        self.frm_right_clear_label = PyLabel(self.frm_right_clear,
                                                  text="Print run"+ " "*size_dict["clear_label_width"],
                                                  font=font)

        self.frm_right_saveprint_btn = PyButton(self.frm_right_clear,
                                                 text="Save Print",
                                                 width=10,
                                                 font=font,
                                                 command=self.__onAutoSaveBtnClick)

        self.frm_right_clear_btn = PyButton(self.frm_right_clear,
                                                 text="Clear Print",
                                                 width=10,
                                                 font=font,
                                                 command=self.__onClearprintBtnClick)


        self.frm_right_clear_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        #self.frm_right_saveprint_btn.grid(row=0, column=1, padx=5, pady=5, sticky="wesn")
        self.frm_right_clear_btn.grid(row=0, column=2, padx=5, pady=5, sticky="wesn")

    def create_frm_status(self):
        self.frm_status_label = PyLabel(self.frm_status,
                                             text="Ready",
                                             font=font)
        self.frm_status_label.grid(row=0, column=0, padx=5, pady=5, sticky="wesn")


    def Reset(self):
        self.frm_right_config.delete("0.0", "end")

    def GetThresholdValue(self, *args):
        try:
            self.thresholdValue = int(self.thresholdStr.get())
        except:
            pass

    def addLog(self, log, tag):
        logging.log(logging.INFO, log)
        if log[-1] != '\n':
            log = log + '\n'

        timeStr = strftime('%H:%M:%S ', localtime(time()))

        self.frm_right_print.configure(state = 'normal')
        self.frm_right_print.insert('end', timeStr + tag + ' ' + log, 'log{0}'.format(self.__lastLogIdx))

        self.__lastLogIdx = self.__lastLogIdx + 1

        if self.__lastLogIdx - self.__firstLogIdx > 1000:
            firstTage = 'log{0}'.format(self.__firstLogIdx)
            firstTageIndex = self.frm_right_print.tag_ranges(firstTage)
            self.frm_right_print.delete(firstTageIndex[0], firstTageIndex[1])
            self.frm_right_print.tag_delete(firstTage)
            self.__firstLogIdx = self.__firstLogIdx + 1

        self.frm_right_print.see('end')

        if self.__lastLogIdx - self.__lastSavedLogIdx > 100:
            self.__saveLog()

        self.frm_right_print.configure(state = 'disabled')

    def __onClearprintBtnClick(self):
        self.__saveLog()

        self.frm_right_print.configure(state = NORMAL)

        firstTage = 'log{0}'.format(self.__firstLogIdx)
        firstTageIndex = self.frm_right_print.tag_ranges(firstTage)
        lastTage = 'log{0}'.format(self.__lastLogIdx - 1)
        lastTageIndex = self.frm_right_print.tag_ranges(lastTage)

        #if not use try, when text is empty, it will report error
        try:
            self.frm_right_print.delete(firstTageIndex[0], lastTageIndex[1])

            while self.__lastLogIdx > self.__firstLogIdx:
                self.frm_right_print.tag_delete(firstTage)
                self.__firstLogIdx = self.__firstLogIdx + 1
                firstTage = 'log{0}'.format(self.__firstLogIdx)
        except:
            pass
        self.frm_right_print.see(END)
        self.frm_right_print.configure(state = DISABLED)


    def __onAutoSaveBtnClick(self):
        if self.__autoSave:
            self.__saveLog()
            self.__autoSave = False
        else:
            self.__autoSavePath = asksaveasfilename(title = 'Save log to',
                                                    defaultextension = 'log',
                                                    filetypes = [('Log files', '*.log'), ('Text files', '*.txt'), ('All files', '*.*')],
                                                    initialdir = self.__settings.get('log_path'),
                                                    initialfile = 'log' + strftime('%Y%m%d-%H%M%S ', localtime(time())))
            if self.__autoSavePath is not None and self.__autoSavePath != '':
                self.__autoSave = True
                self.__saveLog()
                self.__settings.set('log_path', os.path.dirname(self.__autoSavePath))

                self.frm_right_saveprint_btn.configure(state = 'disabled')
        self.__updateAutoSave()

    def __updateAutoSave(self):
        if self.__autoSave:
            self.frm_right_savepath_label["fg"] = "#66CD00"
            self.frm_right_savepath_label['text'] = ('Saved path: ' + self.__autoSavePath)
        else:
            self.frm_right_savepath_label['text'] = ''

    def __saveLog(self):
#        print('auto save {0}, {1}'.format(self.__lastSavedLogIdx, self.__lastLogIdx))
        if self.__autoSaveTimer is not None:
            self.root.after_cancel(self.__autoSaveTimer)

        if not self.__autoSave:
            return

        self.__autoSaveTimer = self.root.after(5000, lambda: self.__saveLog())

        if self.__lastSavedLogIdx >= self.__lastLogIdx \
                or self.__autoSavePath is None \
                or self.__autoSavePath == '':
            return

        file = open(self.__autoSavePath, 'a')
        firstTag = 'log{0}'.format(self.__lastSavedLogIdx)
        firstTagIndex = self.frm_right_print.tag_ranges(firstTag)
        lastTag = 'log{0}'.format(self.__lastLogIdx - 1)
        lastTagIndex = self.frm_right_print.tag_ranges(lastTag)
        try:
            content = self.frm_right_print.get(firstTagIndex[0], lastTagIndex[1])
            file.write(content)
        except:
            #print('test')
            pass
        file.close()
        self.__lastSavedLogIdx = self.__lastLogIdx


    def find_all_serial(self):
        '''
        Get serial list
        '''
        try:
            self.temp_serial = list()
            for com in list_ports.comports():
                strCom = com[0] + ": " + com[1][:-7] #+ ": " + com[1][:-7].decode("gbk").encode("utf-8")
                self.temp_serial.append(strCom)
            for item in self.temp_serial:
                if item not in self.frm_left_listbox.get(0,'end'):
                    self.frm_left_listbox.insert("end", item)

            for item in self.list_box_serial:
                if item not in self.temp_serial:
                    index = list(self.frm_left_listbox.get(0, self.frm_left_listbox.size())).index(item)
                    self.frm_left_listbox.delete(index)
            self.list_box_serial = self.temp_serial

            if self.portselect != None:
                if self.portselect not in self.frm_left_listbox.get(0,'end'):
                    self.portDisconnect = True
                    self.frm_status_label["text"] = "Disconnected [{0}]!".format(self.portselect)
                    self.frm_status_label["fg"] = "red"
                    self.frm_left_open_btn["text"] = "Open"
                    self.frm_left_open_btn['state'] = 'disabled'
                    self.frm_left_open_btn["bg"] = "#008B8B"

            self.thread_findserial = threading.Timer(1, self.find_all_serial)
            self.thread_findserial.setDaemon(True)
            self.thread_findserial.start()
        except Exception as e:
            logging.error(e)

    def Toggle(self):
        '''
        Open or close port
        '''
        if self.frm_left_open_btn["text"] == "Open":
            try:
                self.currentStrCom = self.frm_left_listbox.get(self.frm_left_listbox.curselection())
                self.portselect = self.currentStrCom
                self.port = self.currentStrCom.split(":")[0]
                self.baudrate = self.frm_left_combobox_baudrate.get()
                self.parity = self.frm_left_combobox_parity.get()
                self.databit = self.frm_left_combobox_databit.get()
                self.stopbit = self.frm_left_combobox_stopbit.get()
                self.ser = SerialHelper(Port=self.port,
                                                     BaudRate=self.baudrate,
                                                     ByteSize=self.databit,
                                                     Parity=self.parity,
                                                     Stopbits=self.stopbit)
                self.ser.start()
                if self.ser.alive:
                    self.frm_status_label["text"] = "Open [{0}] Successfully!".format(self.currentStrCom)
                    self.portDisconnect = False
                    self.frm_status_label["fg"] = "#66CD00"
                    self.frm_left_open_btn["text"] = "Close"
                    self.frm_left_open_btn["bg"] = "#F08080"

            except Exception as e:
                logging.error(e)
                try:
                    self.frm_status_label["text"] = "Open [{0}] Failed!".format(self.currentStrCom)
                    self.frm_status_label["fg"] = "#DC143C"
                except Exception as ex:
                    logging.error(ex)

        elif self.frm_left_open_btn["text"] == "Close":
            try:
                self.ser.stop()
                self.receive_count = 0
            except Exception as e:
                logging.error(e)
            self.frm_left_open_btn["text"] = "Open"
            self.frm_left_open_btn["bg"] = "#008B8B"
            self.frm_status_label["text"] = "Close Serial Successfully!"
            self.frm_status_label["fg"] = "#8DEEEE"

    def ClearSettingsbtn(self):
        self.timeonStr.set('')
        self.timeoffStr.set('')
        self.countStr.set('')
        self.count_pause = 0
        self.frm_right_saveprint_btn.configure(state = 'normal')
        self.__autoSave = False
        self.__updateAutoSave()

    def Double_click(self,event):
        self.frm_left_open_btn.configure(state='active')

    def checkBTstatus(self):
        self.addLog('Start to check BT[{0}] connect...'.format(self.btName),'')
        try:
            btCmd = FtpBT(host=self.host, port=self.port, user='', passwd='', btName=self.btName, dataPath=self.dataPath)
        except Exception as e:
            self.addLog('Error when connect FTP: {0}'.format(e),'')
            return False
        status = btCmd.cmd('bluetooth status()')
        if status == '1':
            self.addLog('BT device [%s] connected'%self.btName,'')
            return '1'
        elif status == '0':
            self.addLog('BT device [%s] disconnected!'%self.btName,'')
            return '0'
        elif status == False:
            self.addLog('FTP seems disconnected!!!','')
            return False

    def setWidgetState(self, s):
            self.frm_right_timeon_entry.configure(state = s)
            self.frm_right_timeoff_entry.configure(state = s)
            self.frm_right_count_entry.configure(state = s)
            self.frm_right_clearSettings_btn.configure(state = s)
            self.frm_right_saveprint_btn.configure(state = s)
            self.frm_right_combobox_purpose.configure(state = s)
            self.frm_right_combobox_port.configure(state = s)
            if s == 'disabled':
                self.frm_right_run_btn['text'] = 'Stop'
            elif s == 'normal':
                self.frm_right_run_btn['text'] = 'Run'
            else:
                logging.log(logging.DEBUG, 'Error: no [{0}] state'.format(s))

    def Run(self):
        if (not self.timeonStr.get().isdigit()) or (not self.timeoffStr.get().isdigit()) or (not self.countStr.get().isdigit()):
            self.addLog('Please check your fill in data!!!','')
            return

        if os.path.isfile(self.ini_filename) == False:
            self.addLog("Cannot find configure file Power_cycle.ini",'')
            return
        #if self.ini_filename == None:
        #    self.ini_filename = askopenfilename(title = "Choose Power_cycle.ini",filetypes = [("ini files","*.ini")]) #initialdir = 'C:/',

        if "Power_cycle.ini" not in self.ini_filename:
            self.addLog("Your selected file maybe is wrong! Please choose again!!",'')
            self.runflag = False
            #self.ini_filename = None
            return

        if 'Open' not in self.frm_status_label['text']:
            self.addLog('Please open a COM port!','')
            return

        if 'Successfully' not in self.frm_status_label['text']:
            return

        if self.frm_right_run_btn['text'] == 'Run':
            self.runflag = True
            self.addLog('Running......','')
            self.setWidgetState('disabled')
            self.power_cycle_thread()
        else:
            self.runflag = False
            self.addLog('Stop......','')
            self.setWidgetState('normal')

    def power_cycle_thread(self):
        """
        self.thread_findserial = threading.Timer(3, self.power_cycle_run) #wait 3s to launch, avoid affect main thread(UI)
        self.thread_findserial.setDaemon(True)
        self.thread_findserial.start()
        def power_cycle_run(self):
            while True:
                self.power_cycle()
        """
        self.powerCycleID += 1
        try:
            _thread.start_new_thread(self.power_cycle, ("PowerCycle-{0}".format(self.powerCycleID),) )
        except:
           self.addLog("Error: Cannot start power cycle thread!!!",'')

    def power_cycle(self, threadName):
        if self.runflag == False:
            return
        if os.path.isfile(self.ini_filename) == False:
            self.addLog("Cannot find file Power_cycle.ini",'')
            return
        conf = configparser.ConfigParser()
        try:
            conf.read(self.ini_filename)
            self.host = conf.get("Ftp", "ip")

            self.user = conf.get("Ftp", "user")
            self.passwd = conf.get("Ftp", "passwd")
            self.dataPath = conf.get("Ftp", "dataPath")
            self.btName = conf.get("Device", "btName")

            try:
                self.port = conf.getint("Ftp", "port")
                self.checkBT = conf.getint("Device", "checkBT")
                self.time_press_button_power_on = conf.getint("Device", "time_press_button_power_on")
                self.time_press_button_power_off = conf.getint("Device", "time_press_button_power_off")
            except Exception as e:
                self.addLog("Some config value must be integer: {0}".format(e),'')
                return

        except Exception as e:
            self.addLog("Error when read Power_cycle.ini : {0}".format(e),'')
            return
        if self.ser:
            if self.frm_right_combobox_purpose.get() == 'Button':
                sleep(0.5)
                self.ser.write('50'.encode('utf-8'), isHex=True)
                sleep(0.5)
                self.ser.write('51'.encode('utf-8'), isHex=True)
                sleep(0.5)
                self.ser.write('00'.encode('utf-8'), isHex=True)

            for i in range(self.count_pause+1,int(self.countStr.get())+1):
                if self.runflag == False:
                    return
                self.addLog('-'*37,'')
                self.addLog('This is >>>>>>>>>> %i<<<<<<<<<< times'%i,'')
                self.addLog('Powering on...','')
                self.addLog('Waiting %s seconds'%self.timeonStr.get(),'')

                if self.portDisconnect == False:
                    try:
                        if self.frm_right_combobox_purpose.get() == 'Button':
                            if self.time_press_button_power_on == 0 and self.time_press_button_power_off == 0:
                                self.ser.write(self.frm_right_combobox_port.get().encode('utf-8'), isHex=True)
                            else:
                                self.ser.write(self.frm_right_combobox_port.get().encode('utf-8'), isHex=True)
                                sleep(self.time_press_button_power_on/1000)
                                self.ser.write('00'.encode('utf-8'), isHex=True)
                        else:
                            self.ser.write('B'.encode('utf-8'))
                        sleep(int(self.timeonStr.get()))
                        if self.checkBT == 1:
                            status = self.checkBTstatus()
                            if status == '1':
                                self.addLog('               Power on ------------------------------OK','')
                            elif status == '0':
                                self.addLog('               Power on ------------------------------Failed','')
                            elif status == False:
                                self.addLog('FTP seems disconnected!!!','')
                                self.addLog('Please check your FTP connect and run again!','')
                                return
                    except Exception as e:
                        self.addLog('Error when powering on: {0}'.format(e),'')
                        self.frm_right_run_btn['text'] = 'Run'
                        return
                else:
                    self.addLog('Serial Port seems disconnected......','')
                    self.frm_right_run_btn['text'] = 'Run'
                    return

                #----------------------------------------------------------------------------
                #power off
                if self.runflag == False:
                    return
                self.addLog('Powering off...','')
                self.addLog('Waiting %s seconds'%self.timeoffStr.get(),'')
                if self.portDisconnect == False:
                    try:
                        if self.frm_right_combobox_purpose.get() == 'Button':
                            if self.time_press_button_power_on == 0 and self.time_press_button_power_off == 0:
                                self.ser.write('00'.encode('utf-8'), isHex=True)
                            else:
                                self.ser.write(self.frm_right_combobox_port.get().encode('utf-8'), isHex=True)
                                sleep(self.time_press_button_power_off/1000)
                                self.ser.write('00'.encode('utf-8'), isHex=True)
                        else:
                            self.ser.write('A'.encode('utf-8'))
                        sleep(int(self.timeonStr.get()))
                        if self.checkBT == 1:
                            status = self.checkBTstatus()
                            if status == '1':
                                self.addLog('               Power off -----------------------------Failed','')
                            elif status == '0':
                                self.addLog('               Power off -----------------------------OK','')
                            elif status == False:
                                self.addLog('FTP seems disconnected!!!','')
                                self.addLog('Please check your FTP connect and run again!','')
                                return
                    except Exception as e:
                        self.addLog('Error when powering off: {0}'.format(e),'')
                        self.frm_right_run_btn['text'] = 'Run'
                        return
                else:
                    self.addLog('Serial Port seems disconnected......','')
                    self.frm_right_run_btn['text'] = 'Run'
                    return
                self.addLog('-'*37,'')
            self.setWidgetState('normal')
            self.addLog('Running over......','')


if __name__ == '__main__':
    ui = SerialToolUI()
    ui.mainLoop()
