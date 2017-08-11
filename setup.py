# -*- coding: utf-8 -*-

import sys

from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"], "include_msvcr": True}#, "compressed": True}

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

executables = [
    Executable('SerialRelay.py', base=base)
]

setup(name='Serial_relay',
      version='1.1',
      description='Tymphany SQA power cycle Tool',
      options = {"build_exe": build_exe_options},
      executables=executables
      )
