#!/usr/bin/env python
# -*- coding:utf-8 -*-

import urllib.request
import os
import sys
import time
import json
from typing import Dict, Any, Callable
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

json_dir_from_home = "Library/Application Support/Google Play Music Desktop Player/json_store/"
json_path_from_home = "Library/Application Support/Google Play Music Desktop Player/json_store/playback.json"
json_dir = os.path.join(os.environ["HOME"], json_dir_from_home)
json_path = os.path.join(os.environ["HOME"], json_path_from_home)


def token_env_val() -> str:
    token = os.environ.get("SLACK_TOKEN")
    if token:
        return token
    else:
        print("set environment variable 'SLACK_TOKEN'")
        os._exit(1)


class PlaybackHandler(FileSystemEventHandler):

    def __init__(self) -> None :
        super().__init__()
        self.prev_title: str = ""
        self.prev_artist: str = ""
        self.prev_album: str = ""

    @staticmethod
    def playback_of_gpmdp() -> Dict[str, Dict[str, str]]:

        # IOError
        with open(json_path, "r") as f:
            playback = json.load(f)
            return playback

    def __post_status(self, title: str, artist: str) -> None:
        token = token_env_val()

        url = "https://slack.com/api/users.profile.set"
        method = "POST"
        # headers = {"Content-Type" : "application/json"}
        # ボディにJSONいれても聞いてくれないので、クエリの形に

        obj = {"token": token, "profile": {"status_text": f"Now Playing... Title: {title}, Artist: {artist}", "status_emoji": ":google_assistant:"}}
        data = urllib.parse.urlencode(obj).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method)
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")

        write_log(response_body)

        # if response ok
        self.prev_title = title
        self.prev_artist = artist

    def __update_slack_status(self, playback: Dict[str, Dict[str, str]]) -> None:
        title: str = playback["song"]["title"]
        artist: str = playback["song"]["artist"]
        if artist == self.prev_artist and title == self.prev_title:
            # self.prev_title = title
            # self.prev_artist = artist
            return

        self.__post_status(title, artist)

    def on_modified(self, event: Any) -> None:
        # decode出来ないかも知れないのはoptionalで表現したい
        try:
            self.__update_slack_status(self.playback_of_gpmdp())
        except json.decoder.JSONDecodeError:
            print("cannot decode json :(")


def main() -> None:
    event_handler = PlaybackHandler()
    observer = Observer()
    observer.schedule(event_handler, json_dir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def is_parent(pid: int) -> bool:
    return bool(pid)


def parricide(pid: int) -> None:
    if is_parent(pid):
        sys.exit()


def throw_away_io() -> None:
    stdin = open(os.devnull, 'rb')
    stdout = open(os.devnull, 'ab+')
    stderr = open(os.devnull, 'ab+', 0)

    for (null_io, std_io) in zip((stdin, stdout, stderr), (sys.stdin, sys.stdout, sys.stderr)):
        os.dup2(null_io.fileno(), std_io.fileno())


def write_pid(pid: int) -> None:
    if is_parent(pid):
        with open(os.path.join(os.environ["HOME"], 'var/run/set_statusd.pid'), 'w') as f:
            f.write(f"{pid}\n")


def write_log(message: str) -> None:
    with open(os.path.join(os.environ["HOME"], 'set_statusd.log'), 'a') as f:
        f.write(f"{datetime.today().strftime('%Y-%m-%d %H:%M:%S')} {message}\n")


def daemonize(callback: Callable) -> None:
    first_pid: int = os.fork()
    parricide(first_pid)
    os.setsid()
    second_pid: int = os.fork()
    write_pid(second_pid)
    parricide(second_pid)
    throw_away_io()
    callback()


if __name__ == '__main__':
    # daemonize(main)
    # leave daemonize to launchd
    main()
