#!/usr/bin/env python
# -*- coding:utf-8 -*-

import urllib.request
import os
import sys
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

json_dir_from_home = "Library/Application Support/Google Play Music Desktop Player/json_store/"
json_path_from_home = "Library/Application Support/Google Play Music Desktop Player/json_store/playback.json"
json_dir = os.path.join(os.environ["HOME"], json_dir_from_home)
json_path = os.path.join(os.environ["HOME"], json_path_from_home)

class PlaybackHandler(FileSystemEventHandler):

    def __init__(self):
        super().__init__()
        self.prev_title = None
        self.prev_artist = None
        self.prev_album = None

    @staticmethod
    def playback_of_gpmdp():

        # IOError
        with open(json_path, "r") as f:
            playback = json.load(f)
            return playback

    def __post_status(self, title, artist):
        # error handling
        token = os.environ["SLACK_TOKEN"]

        url = "https://slack.com/api/users.profile.set"
        method = "POST"
        # headers = {"Content-Type" : "application/json"}
        # ボディにJSONいれても聞いてくれないので、クエリの形に

        obj = {"token": token, "profile": {"status_text": f"Now Playing... Title: {title}, Artist: {artist}" , "status_emoji": ":vivaldi:"}}
        data = urllib.parse.urlencode(obj).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method)
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")

        print(response_body)

        # if response ok
        self.prev_title = title
        self.prev_artist = artist

    def __update_slack_status(self, playback):
        title = playback["song"]["title"]
        artist = playback["song"]["artist"]
        if artist == self.prev_artist and title == self.prev_title:
            # self.prev_title = title
            # self.prev_artist = artist
            return

        self.__post_status(title, artist)

    def on_modified(self, event):
        self.__update_slack_status(self.playback_of_gpmdp())

# import pdb; pdb.set_trace()
# 二段階の認証でつまった

def daemon_main():
    event_handler = PlaybackHandler()
    observer = Observer()
    observer.schedule(event_handler, json_dir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(15)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def fork():
        pid = os.fork()
        if pid > 0:
                f = open('/var/run/set_statusd.pid', 'w')
                f.write(str(pid)+"\n")
                f.close()
                sys.exit()

        if pid == 0:
                daemon_main()

if __name__=='__main__':
        fork()

