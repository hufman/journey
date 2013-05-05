#!/usr/bin/env python
import sys
import smidi

filename='8m3_1.mid'
if len(sys.argv)>1:
	filename = sys.argv[1]
a=smidi.MidiInFile(smidi.MidiToText(), filename)
a.read()

