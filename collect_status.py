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
        print('[INFO]', s)

        # Flush to make it apeear immediately in automation log.
        sys.stdout.flush()

    @classmethod
    def fetch(cls, url):
        cls.info(f'Fetching {url}')


class TaskCluster:
    API_URL = 'https://firefox-ci-tc.services.mozilla.com/api/'

    @classmethod
    def url(cls, name):
        return f'{cls.API_URL}{name}'

    @classmethod
    def call(cls, name):
        url = cls.url(name)
        Logger.fetch(url)
        req = urllib.request.Request(url, None, {
            'User-Agent': 'areweesmifiedyet',
        })
        response = urllib.request.urlopen(req)
        return response.read()

    @classmethod
    def call_json(cls, name):
        return json.loads(cls.call(name))

    @classmethod
    def task(cls, task_id, retry_id):
        return cls.call_json(f'queue/v1/task/{task_id}/runs/{retry_id}/artifacts')['artifacts']

    @classmethod
    def artifact(cls, task_id, retry_id, name):
        return cls.url(f'queue/v1/task/{task_id}/runs/{retry_id}/artifacts/{name}')

    @classmethod
    def artifact_json(cls, task_id, retry_id, name):
        return cls.call_json(f'queue/v1/task/{task_id}/runs/{retry_id}/artifacts/{name}')


class TreeHerder:
    API_URL = 'https://treeherder.mozilla.org/api/'

    @classmethod
    def url(cls, name):
        return f'{cls.API_URL}{name}'

    @classmethod
    def call(cls, name):
        url = cls.url(name)
        Logger.fetch(url)
        req = urllib.request.Request(url, None, {
            'User-Agent': 'areweesmifiedyet',
        })
        response = urllib.request.urlopen(req)
        return response.read()

    @classmethod
    def call_json(cls, name):
        return json.loads(cls.call(name))

    @classmethod
    def jobs(cls, push_id):
        push = cls.call_json(f'jobs/?push_id={push_id}&format=json')
        count = push['count']
        results = []
        results += push['results']

        page = 2
        while len(results) < count:
            push = cls.call_json(f'jobs/?push_id={push_id}&format=json&page={page}')
            results += push['results']
            page += 1

        return results

    @classmethod
    def job(cls, id):
        return cls.call_json(f'project/mozilla-central/jobs/{id}/')

    @classmethod
    def find_job(cls, name):
        pushes = cls.call_json("project/mozilla-central/push/?full=true&count=10")
        for result in pushes['results']:
            jobs = cls.jobs(result['id'])

            for job in jobs:
                if name in job:
                    return cls.job(job[1]), result['revision']

        return None, None

    @classmethod
    def find_artifact_json(cls, job, name):
        task_id = job['task_id']
        retry_id = job['retry_id']

        for item in TaskCluster.task(task_id, retry_id):
            if item['name'] == name:
                return TaskCluster.artifact_json(task_id, retry_id, item['name'])

        return None


class StatusUpdater:
    def run():
        job_name = 'are-we-esmified-yet-check'
        artifact_name = 'public/are-we-esmified-yet.json'

        Logger.info('Loading log')

        log_file = './log.json'
        if pathlib.Path(log_file).exists():
            with open(log_file, 'r') as f:
                log_data = json.loads(f.read())
        else:
            log_data = []

        if len(log_data) > 0:
            last_date = log_data[-1]["date"]
        else:
            last_date = None

        Logger.info('Finding latest artifact')

        job, rev = TreeHerder.find_job(job_name)
        if not job:
            Logger.info('No job found')
            return

        t = job['submit_timestamp']
        d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc)
        date = d.strftime('%Y-%m-%d')

        if last_date == date:
            Logger.info('The latest artifact is from the same date')
            return

        artifact = TreeHerder.find_artifact_json(job, artifact_name)
        if not job:
            Logger.info('No artifact found')
            return

        Logger.info('Saving log')

        artifact['hash'] = rev
        artifact['date'] = date

        log_data.append(artifact)

        with open(log_file, 'w') as f:
            f.write(json.dumps(log_data))


StatusUpdater.run()
