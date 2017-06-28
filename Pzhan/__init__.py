#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging

logging.basicConfig(level=logging.INFO)
console_log = logging.StreamHandler()
console_log.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                                           datefmt='%Y-%m-%d %H:%M:%S'))

log = logging.getLogger()
log.addHandler(console_log)




