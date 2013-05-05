#!/usr/bin/env python
import sys
import smidi

class ReadData(smidi.MidiOutStream):
	def __init__(self):
		self.events = []
	def convert_clocks(self, clocks):
		""" to beats """
		return round(1.0 * clocks / self.division)
	def convert_beats(self, beats):
		""" to seconds """
		bpm = 60000000.0 / self.midi_tempo
		bps = bpm / 60
		return beats / bps
	def get_event(self):
		beat = self.convert_clocks(self.abs_time())
		return {"beat":beat, "secs":self.convert_beats(beat)}
	def header(self, format=0, nTracks=1, division=96):
		self.division = division
		print("Division %s"%division)
	def tempo(self, value):
		self.midi_tempo = value
		print("Tempo %s"%value)
	def time_signature(self, nn, dd, cc, bb):
		den = pow(2, dd)
		self.num = nn
		self.den = den
		self.cc = cc
		self.bb = bb
		print("Time %s/%s"%(nn,den))
		print("Clocks for metronome: %s"%cc)
		print("32nd notes per midi quarter: %s"%bb)
	def marker(self, marker):
		if marker == 'X-1':
			print("Transition at %s"%self.abs_time())
		elif marker == 'XM1':
			print("Transition done at %s"%self.abs_time())
		elif marker == 'X0':
			print("Mark Off at %s"%self.abs_time())
		else:
			print("Unknown mark %s at %s"%(marker, self.abs_time()))
		event = self.get_event()
		event['marker'] = marker
		self.events.append(event)
	def eof(self):
		event = self.get_event()
		event['eof'] = True
		self.events.append(event)


#filename='8m3_1.mid'
#a=smidi.MidiInFile(smidi.MidiToText(), filename)
#a.read()

reader=ReadData()
filename='8m3_1.mid'
if len(sys.argv)>1:
	filename = sys.argv[1]
a=smidi.MidiInFile(reader, filename)
a.read()
print(reader.events)

