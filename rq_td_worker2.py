#!/usr/bin/python3

# -*- coding: utf-8 -*-
import re
import sys

from rq.cli import worker
import mreq

if __name__ == '__main__':
	print("worker")
	if len(sys.argv) == 1:
		sys.argv = ['./rqworker2.py', 'listeners', '--url', 'redis://127.0.0.1:6383']
	sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
	sys.exit(worker())

