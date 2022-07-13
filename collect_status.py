#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import json
import pathlib
import re
import subprocess
import sys
import urllib.request


class Logger:
    @classmethod
    def info(cls, s):
        print("[INFO]", s)

        # Flush to make it apeear immediately in automation log.
        sys.stdout.flush()

    @classmethod
    def fetch(cls, url):
        cls.info(f"Fetching {url}")


class TaskCluster:
    API_URL = "https://firefox-ci-tc.services.mozilla.com/api/"

    @classmethod
    def url(cls, route, artifact):
        return f"{cls.API_URL}index/v1/task/{route}/artifacts/{artifact}"

    @classmethod
    def call(cls, route, artifact):
        url = cls.url(route, artifact)
        Logger.fetch(url)
        req = urllib.request.Request(url, None, {
            "User-Agent": "areweesmifiedyet",
        })
        response = urllib.request.urlopen(req)
        return response.read()

    @classmethod
    def call_json(cls, route, artifact):
        return json.loads(cls.call(route, artifact))


class StatusUpdater:
    def run():
        job_name = "are-we-esmified-yet-check"
        route_name = "gecko.v2.mozilla-central.latest.firefox.are-we-esmified-yet"
        artifact_name = "public/are-we-esmified-yet.json"

        Logger.info("Loading log")

        log_file = "./log.json"
        if pathlib.Path(log_file).exists():
            with open(log_file, "r") as f:
                log_data = json.loads(f.read())
        else:
            log_data = []

        if len(log_data) > 0:
            last_date = log_data[-1]["date"]
        else:
            last_date = None

        artifact = TaskCluster.call_json(route_name, artifact_name)

        date = artifact["date"]

        if last_date == date:
            Logger.info("The latest artifact is from the same date")
            return

        Logger.info("Saving log")

        log_data.append(artifact)

        with open(log_file, "w") as f:
            f.write(json.dumps(log_data))


StatusUpdater.run()
