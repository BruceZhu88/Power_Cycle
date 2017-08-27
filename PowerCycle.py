#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading

from UI import SerialTool


if __name__ == '__main__':
    
    ui = SerialTool.SerialToolUI()
    main = threading.Thread(target=ui.mainLoop())
    threads = []
    threads.append(main)
    threads[0].start()
