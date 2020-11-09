#!/bin/python3
import os
import sys
import argparse
import json
import time
import lz4.block
from tabulate import tabulate
from datetime import datetime as dt

sys.path.insert(0, '{}/{}'.format(os.getcwd(), 'src'))
from portable_funcs import *

version = 0.1

#https://gist.github.com/snorey/3eaa683d43b0e08057a82cf776fd7d83
def mozlz4_to_dict(filepath):
	# Given the path to a "mozlz4", "jsonlz4", "baklz4" etc. file,
	# return the uncompressed text.
	bytestream = open(filepath, 'rb')
	bytestream.read(8)	# skip past the b"mozLz40\0" header
	valid_bytes = bytestream.read()
	text = lz4.block.decompress(valid_bytes)
	return json.loads(text.decode('utf-8'))

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--add', help="Store current session", metavar='session_name', default=None, type=str)
parser.add_argument('-r', '--remove', help="Remove stored session", metavar='session_name', default=None, type=str)
parser.add_argument('-u', '--update', help="Update session with current state", metavar='session_name', default=None, type=str)
parser.add_argument('-o', '--open', help="Open session", metavar='session_name', default=None, type=str)
parser.add_argument('-l', '--list', help="List stored sessions", default=False, action='store_true')
parser.add_argument('-c', '--check', help="Check and display actual session", default=False, action='store_true')
parser.add_argument('-v', '--verbose', default=False, action='store_true')
parser.add_argument('-V', '--version', default=False, action='store_true', help="Show version and exit")
parser.add_argument('--sessions-file', help="Specify file to store sessions", default=None, metavar='file', type=str)
parser.add_argument('--config-sessions-file', help="Set default sessions file", metavar='file', type=str)
parser.add_argument('--window-delay', help="Set window open delay (usefull in windows systems)", metavar='seconds', default=None, type=int)
parser.add_argument('--config-window-delay', default=None, type=int, help="Set default window open delay")
parser.add_argument('--tabs-delay', help="Set tabs open delay (usefull in windows systems)", metavar='seconds', default=None, type=int)
parser.add_argument('--config-tabs-delay', default=None, type=int, help="Set default tabs open delay")
args = parser.parse_args()

#Version flag
if args.version: sys.exit('Firefox Session Manager v{}'.format(version))

#Ensure config folder is available
separator = '/' if sys.platform == 'linux' else '\\'
cf_location = config_file_location()
config_path = separator.join(cf_location.split(separator)[:-1])
if not os.path.isdir(config_path):
	os.makedirs(config_path, exist_ok = True)
	if args.verbose: print('Created folder {}'.format(config_path))

#Read (and update if required) the config file
if os.path.isfile(cf_location):
	with open(cf_location, 'r') as f: cfg = json.load(f)

	if args.config_sessions_file is not None: cfg['sessions_file'] = os.path.expanduser(args.config_sessions_file)
	if args.config_window_delay is not None: cfg['window_delay'] = args.config_window_delay
	if args.config_tabs_delay is not None: cfg['tabs_delay'] = args.config_tabs_delay

	if any([args.config_sessions_file is not None, args.config_window_delay is not None, args.config_tabs_delay is not None]):
		with open(cf_location, 'w') as f: f.write('{}\n'.format(json.dumps(cfg, indent = 4)))
		if args.verbose: print('Updated config file at {}'.format(cf_location))

#Create the config file
else:
	cfg = {
		'sessions_file' : DEFAULTS.SESSION_FILE if args.config_sessions_file is None else os.path.expanduser(args.config_sessions_file),
		'window_delay' : DEFAULTS.WINDOW_DELAY if args.config_window_delay is None else args.config_window_delay,
		'tabs_delay' : DEFAULTS.TABS_DELAY if args.config_tabs_delay is None else args.config_tabs_delay
	}
	with open(cf_location, 'w') as f: f.write('{}\n'.format(json.dumps(cfg, indent = 4)))
	if args.verbose: print('Created config file at {}'.format(cf_location))

#Update params with their defaults if not provided
if args.sessions_file is None: args.sessions_file = cfg['sessions_file']
if args.window_delay is None: args.window_delay = cfg['window_delay']
if args.tabs_delay is None: args.tabs_delay = cfg['tabs_delay']

#Ensure sessions file is available
if not os.path.isfile(args.sessions_file):
	with open(args.sessions_file, 'w') as f: f.write('{}\n')
	if args.verbose: print('Sessions file initialized at {}'.format(args.sessions_file))

#Read sessions
with open(args.sessions_file, 'r') as f: sessions = json.load(f)

#List flag
if args.list:
	d = [["session_name", "last_updated", "num_windows", "num_tabs"]] + [
		[session_name, sessions[session_name]['last_updated'], len(sessions[session_name]['windows']), sum(len(w) for w in sessions[session_name]['windows'])]
	for session_name in sorted(sessions.keys(), key = lambda s: dt.strptime(sessions[s]['last_updated'], "%Y/%m/%d %H:%M:%S"), reverse=True)]
	print(tabulate(d, tablefmt="grid"))

#Add and update flags
if args.add or args.update or args.check:
	d = mozlz4_to_dict(get_firefox_session_file())
	entry = {
		'last_updated' : dt.now().strftime("%Y/%m/%d %H:%M:%S"),
		'windows' : [[t['entries'][-1]['url'] for t in w['tabs']] for w in d['windows']]
	}

	if args.check:
		for i,w in enumerate(entry['windows']):
			print('Window {}:'.format(i + 1))
			for url in w: print('\t{}'.format(url))
	else:
		session_name = args.add or args.update
		if args.add and session_name in sessions: sys.exit('Session {} already exists'.format(session_name))

		sessions[session_name] = entry
		with open(args.sessions_file, 'w') as f: f.write(json.dumps(sessions, indent = 4))
		if args.verbose: print("Saved current session as {}".format(session_name))

#Remove flag
if args.remove:
	if args.remove not in sessions: sys.exit('Session {} does not exists'.format(args.remove))

	del sessions[args.remove]
	with open(args.sessions_file, 'w') as f: f.write(json.dumps(sessions, indent = 4))
	if args.verbose: print("Removed stored session {}".format(args.remove))

#Open flag
if args.open:
	if args.open not in sessions: sys.exit('Session {} does not exists'.format(args.open))
	if args.verbose: print("Opening stored session {}...".format(args.open))

	for i,w in enumerate(sessions[args.open]['windows']):
		if args.verbose: print("Opening window to {}...".format(w[0]))
		open_window(w[0], args.window_delay)

		for url in w[1:]:
			if args.verbose: print("Opening tab to {}...".format(url))
			open_tab(url)

		if i < len(sessions[args.open]['windows']) - 1:
			time.sleep(args.tabs_delay)
