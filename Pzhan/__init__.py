#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging

logging.basicConfig(level=logging.DEBUG)
console_log = logging.StreamHandler()
console_log.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'),
                         datefmt='%a, %d %b %Y %H:%M:%S')

log = logging.getLogger()
log.addHandler(console_log)




