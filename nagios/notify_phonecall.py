#!/usr/bin/python

import sys
import urllib


if __name__ == '__main__':
	from optparse import OptionParser
	parser = OptionParser()
	parser.add_option("-H", 	dest="host",	type='string')
	parser.add_option("-s", 	dest="state",	type='string')
	parser.add_option("-S", 	dest="service",	type='string', default=None)
	parser.add_option("-p", 	dest="phone",	type='string')

	(options, args) = parser.parse_args()

	strHost = options.host
	import re
	strHost = re.sub(r'(\w+)(\d+)(\w*)', r'\1 \2 \3', strHost)
	if strHost.endswith(' a'):
		strHost+='lpha'
	elif strHost.endswith(' b'):
		strHost+='eta'

	if options.service:
		strMsg = "Service %s on host %s is %s"%(options.service, strHost, options.state)
	else:
		strMsg = "Host %s is %s"%(strHost, options.state)
	strURL = 'http://APPID.appspot.com/alert?number=%s&msg=%s'%(options.phone, urllib.quote(strMsg))
	urllib.urlopen(strURL)
