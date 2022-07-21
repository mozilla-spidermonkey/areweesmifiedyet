#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json

log_file = "./log.json"
with open(log_file, "r") as f:
    log_data = json.loads(f.read())

for data in log_data:
    print(data['date'])
