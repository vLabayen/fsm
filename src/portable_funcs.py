import os
import sys
import webbrowser
import subprocess as sp
import time

def default_sfile():
	if sys.platform == 'linux': return os.path.expanduser("~/.fsm/sessions.json")
	elif sys.platform == 'win32': return os.path.expanduser("~\\.fsm\\sessions.json")

	raise ValueError('Current platform ({}) is not supported'.format(sys.platform))

def config_file_location():
	if sys.platform == 'linux': return os.path.expanduser("~/.fsm/fsm.conf")
	elif sys.platform == 'win32': return os.path.expanduser("~\\.fsm\\fsm.conf")

	raise ValueError('Current platform ({}) is not supported'.format(sys.platform))

def get_firefox_session_file():
	if sys.platform == 'linux': path = os.path.expanduser('~/.mozilla/firefox')
	elif sys.platform == 'win32': path = os.path.expanduser('~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles')
	else: raise ValueError('Current platform ({}) is not supported'.format(sys.platform))

	separator = '/' if sys.platform == 'linux' else '\\'

	for f in os.listdir(path):
		if 'default-release' in f:
			return '{path}{separator}{file}{separator}sessionstore-backups{separator}recovery.jsonlz4'.format(path=path, separator=separator, file=f)

def open_window(url, sleep_time):
	# webbrowser.open_new does not open the second browser on windows
	if sys.platform == 'linux': webbrowser.open_new(url)
	elif sys.platform == 'win32': sp.Popen(['C:\\Program Files\\Mozilla Firefox\\firefox.exe', '--new-window', url])
	else: raise ValueError('Current platform ({}) is not supported'.format(sys.platform))

	time.sleep(sleep_time)

def open_tab(url): webbrowser.open_new_tab(url)


class DEFAULTS:
	SESSION_FILE = default_sfile()
	WINDOW_DELAY = 3 if sys.platform != 'linux' else 0
	TABS_DELAY = 5 if sys.platform != 'linux' else 0
