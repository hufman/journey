#!/usr/bin/env python

import struct
import smidi
import pydub

options = {
	'loop_counts': [1,0,1,1],
	'loop_transitions': [4, 1, 2, 9],
	'skip_secondloop': False,
	'secondloop_fade': False,
	'skip_8m3_8': False	# for the soundtrack version
}

options_apotheosis = {
	'loop_counts': [0,0,0,0],
	'loop_transitions': [5, 3, 4, 11],
	'early_8m3_2': 8,
	'early_8m3_3_4': 8,
	'thirdloop_hard': True,
	'delay_8m3_10': True,
	'skip_secondloop': False,
	'secondloop_fade': True,
	'skip_8m3_8': True
}

options_lzh234 = {
	'loop_counts': [0,0,0,0],
	'loop_transitions': [4, 0, 2, 9],
	'early_8m3_3_4': 16,
	'skip_secondloop': True,
	'secondloop_fade': True,
	'skip_8m3_8': False
}

options_silentqix = {
	'loop_counts': [2,0,1,1],
	'loop_transitions': [2, 2, 0, 3],
	'skip_secondloop': False,
	'secondloop_fade': False,
	'skip_8m3_8': False	# for the soundtrack version
}

defines = {
	'bpm': 108,
	# fadeout - play once, start next when see the X0 marker
	# loop - play repeatedly, X-1 markers start next song and XM1 stop current
	# jumpout - play repeatedly, start next song any 4 beats and fade out after 8
	'files': ['8m3_1', '8m3_2', '8m3_3_4', '8m3_5',
	          '8m3_6' ,'8m3_7', '8m3_8', '8m3_9',
	          '8m3_10', '8m3_11'],
	'types': {'8m3_1':'fadeout', '8m3_2':'loop', '8m3_3_4':'fadeout',
	        '8m3_5':'jumpout', '8m3_6':'fadeout', '8m3_7':'loop',
	        '8m3_8':'fadeout', '8m3_9':'jumpout', '8m3_10':'fadeout', '8m3_11':'none'},
	'loop_fadeouts': [8, 8, 8, 4],
	'filetype': 'mp3',
	'fileext': 'xvag'
}

class ReadMidiData(smidi.MidiOutStream):
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
	def tempo(self, value):
		self.midi_tempo = value
	def time_signature(self, nn, dd, cc, bb):
		den = pow(2, dd)
		self.num = nn
		self.den = den
		self.cc = cc
		self.bb = bb
	def marker(self, marker):
		event = self.get_event()
		event['marker'] = marker
		self.events.append(event)
	def eof(self):
		event = self.get_event()
		event['eof'] = True
		self.events.append(event)

# Helper method to get exact frames, used for trimming
def get_frames(self, start, end):
	start = start * self.frame_width
	end = end * self.frame_width
	return self._spawn(self._data[start:end])
pydub.AudioSegment.get_frames = get_frames

def beats_to_ms(beats):
	bps = defines['bpm'] / 60.0
	return int((beats / bps) * 1000)

def audio_frame_ms(audio, frame):
	""" given a frame index in the audio file, return the ms """
	fps = audio.frame_rate
	return int(1.0 * frame / fps * 1000.0)

def ltrim_audio(audio):
	laststart = 0	# last zero sample
	start = 0	# first nonzero sample
	nonzeros = 0
	sample = struct.unpack("<f", audio.get_frame(start))
	while nonzeros < 2:
		start += 1
		sample = struct.unpack("<f", audio.get_frame(start))[0]
		if sample == 0.0:
			nonzeros = 0
			laststart = start
		else:
			nonzeros += 1
	ms = audio_frame_ms(audio, laststart)
	return audio.get_frames(laststart, int(audio.frame_count()))
def rtrim_audio(audio):
	frames = int(audio.frame_count())
	lastend = frames - audio.channels	# last zero sample
	end = frames - audio.channels		# first nonzero sample
	nonzeros = 0
	sample = struct.unpack("<f", audio.get_frame(end))
	while nonzeros < 2:
		end -= 1
		sample = struct.unpack("<f", audio.get_frame(end))[0]
		if sample == 0.0:
			nonzeros = 0
			lastend = end
		else:
			nonzeros += 1
	ms = audio_frame_ms(audio, lastend)
	return audio.get_frames(0, lastend)
	return audio[0:ms]

def trim_audio(audio):
	return rtrim_audio(ltrim_audio(audio))

def render(options, export, format):
	output = {
		"data": None,
		"position": 0
	}
	loops = -1
	def add_audio(audio, amount):
		""" Add the given audio segment to the output
		Leave the position set so that the unfinished ms can be overwritten
		"""
		print("Adding %s(%s/%s) at %s"%(file, amount, len(audio), output['position']))
		if output['data'] == None:
			output['data'] = audio
		else:
			#output['data'] = output['data'].overlay(audio, output['position'])
			subposition = len(output['data']) - output['position']
			if subposition > 0:
				output['data'] = output['data'].overlay(audio[0:subposition], output['position'])
			if len(audio) > subposition:
				output['data'] = output['data'].append(audio[subposition:], 0)

		output['position'] = output['position'] + amount
		#output['position'] -= 8		# hack for gaplessness
	for file in defines['files']:
		type = defines['types'][file]
		reader = ReadMidiData()
		smidi.MidiInFile(reader, file+".mid").read()
		endmarker = [x for x in reader.events if x.has_key('eof')][0]
		audio = pydub.AudioSegment.from_file(file+'.'+defines['fileext'], defines['filetype'])
		#import ipdb; ipdb.set_trace()
		if options['skip_8m3_8'] and file == '8m3_8':
			continue
		if options.has_key('delay_8m3_10') and file == '8m3_10':
			output['position'] += 100
		if type == 'fadeout':
			fademarker = [x for x in reader.events if x.has_key('marker') and x['marker'] == 'X0'][0]
			fadebeat = fademarker['beat']
			if options.has_key('early_'+file):
				fadebeat -= options['early_'+file]
			fadems = beats_to_ms(fadebeat)
			if file == '8m3_1':
				fadems += 111
			add_audio(audio, fadems)
		if type == 'loop':
			oldlen = len(audio)
			audio = trim_audio(audio)
			newlen = len(audio)

			loops += 1
			time = len(audio) * options['loop_counts'][loops]
			earlybeat = options['early_'+file] if options.has_key('early_'+file) else 0
			transitions = [x for x in reader.events if x.has_key('marker') and x['marker'] == 'X-1']
			if options['loop_transitions'][loops] >= len(transitions):
				nextbeat = endmarker['beat'] - earlybeat
				nextms = len(audio) - beats_to_ms(earlybeat)
				stopms = beats_to_ms(nextbeat + defines['loop_fadeouts'][loops])
				nextms = beats_to_ms(nextbeat)
				if options.has_key('thirdloop_hard'):
					stopms = nextms
			else:
				transition = transitions[options['loop_transitions'][loops]]
				fadeouts = [x for x in reader.events if x.has_key('marker') and x['marker'] == 'XM1']
				fadeouts = [x for x in fadeouts if x['beat'] > transition['beat']]
				if False and len(fadeouts) > 0:		# it seems to ignore the fadeout marks
					stopms = beats_to_ms(fadeouts[0]['beat'] - earlybeat)
				else:
					stopms = beats_to_ms(transition['beat'] - earlybeat + defines['loop_fadeouts'][loops])
				nextms = beats_to_ms(transition['beat'] - earlybeat)
			stopms = time + stopms
			nextms = time + nextms
			while stopms > 0:
				increment = min(len(audio), stopms)
				amount = min(len(audio), nextms)
				amount = max(0, amount)
				stopms -= len(audio)
				nextms -= len(audio)
				add_audio(audio[0:increment], amount)
			output['position'] -= (oldlen - newlen)
			
		if type == 'jumpout':
			oldlen = len(audio)
			audio = trim_audio(audio)
			newlen = len(audio)

			loops += 1
			if options['skip_secondloop'] and loops == 1:
				continue
			options['loop_counts'][1] = 0	# this one sounds bad if looped
			time = len(audio) * options['loop_counts'][loops]
			transitions = range(0, int(endmarker['beat']), 4)
			if options['loop_transitions'][loops] >= len(transitions):
				stopms = len(audio) + beats_to_ms(defines['loop_fadeouts'][loops])
				nextms = len(audio)
			else:
				transition = transitions[options['loop_transitions'][loops]]
				stopms = beats_to_ms(transition + defines['loop_fadeouts'][loops])
				nextms = beats_to_ms(transition)
				if not options['secondloop_fade'] and loops == 1 and stopms <= beats_to_ms(endmarker['beat']):
					stopms = len(audio)
			stopms = time + stopms
			nextms = time + nextms
			while stopms > 0:
				increment = min(len(audio), stopms)
				amount = min(len(audio), nextms)
				amount = max(0, amount)
				stopms -= len(audio)
				nextms -= len(audio)
				add_audio(audio[0:increment], amount)
			output['position'] -= (oldlen - newlen)
		if type == 'none':
			add_audio(audio, len(audio))
	print("Exporting")
	output['data'].export(export, format=format)

if __name__ == '__main__':
	#render(options_apotheosis, 'apotheosis.mp3', 'mp3')
	#render(options_lzh234, 'lzh.mp3', 'mp3')
	#render(options_silentqix, 'silentqix.mp3', 'mp3')
	render(options, 'custom.mp3', 'mp3')
