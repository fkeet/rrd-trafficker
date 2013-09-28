#!/usr/bin/env python
import sys
import yaml
import re
import os
import rrdtool
import logging as log

FILE = '/tmp/'
step = 300
heartbeat = step * 2

line = sys.stdin.readline()
# Process each line in the data
while line:
    # Preprocess the line
    line = line.strip()
    tokens = line.split(' ')

    # If the line looks like a valid line:
    if "IP:" in tokens and len(tokens) > 6:
        # Extract relevant data
        ip = tokens[1]
        traffic_in = tokens[6]
        traffic_out = tokens[-1]
        filename = os.path.join(FILE, ip + '.rrd')

        # If we have no data file for this ip, create one
        if not os.path.exists(filename):
            log.info('Creating new data file for %s', ip)
            rrdtool.create(filename,
                "--step", str(step), "--start", "0",
                "DS:input:COUNTER:%s:U:U" % str(heartbeat),
                "DS:output:COUNTER:%s:U:U" % str(heartbeat),
                "RRA:AVERAGE:0.5:1:600",
                "RRA:AVERAGE:0.5:12:24",
                "RRA:AVERAGE:0.5:288:7",
                "RRA:AVERAGE:0.5:2016:30",
                "RRA:AVERAGE:0.5:60480:12",
                "RRA:MAX:0.5:12:24",
                "RRA:MAX:0.5:288:7",
                "RRA:MAX:0.5:2016:30",
                "RRA:MAX:0.5:60480:12",
                )

        # Update the file with the new data
        traffic_in = 0
        traffic_out = 0
        import random
        traffic_in += random.randrange(1000, 1500)
        traffic_out += random.randrange(1000, 3000)
        print(filename, 'N:' + str(traffic_in) + ':' + str(traffic_out))

        ret = rrdtool.update(filename,
            'N:' + str(traffic_in) + ':' + str(traffic_out))
        if ret:
            print rrdtool.error()

        rrdtool.graph(filename + '.png',
            '--imgformat', 'PNG',
            '--width', '540',
            '--height', '100',
            '--start', "end-300s",
            '--end', "now",
            '--vertical-label', 'Bytes/Second',
            '--title', 'Traffic for %s' % ip,
            '--lower-limit', '0',
            'DEF:in_bytes=%s:input:AVERAGE' % filename,
            'DEF:out_bytes=%s:output:AVERAGE' % filename,
            'AREA:in_bytes#990033:Download',
            'LINE1:out_bytes#990033:Upload',
            )
        ret = rrdtool.graph("net.png",
            "--start", "end-1h", "--vertical-label=Bytes/s",
            "DEF:inoctets=%s:input:AVERAGE" % filename,
            "DEF:outoctets=%s:output:AVERAGE" % filename,
            "AREA:inoctets#00FF00:In traffic",
            "LINE1:outoctets#0000FF:Out traffic\\r",
            "CDEF:inbits=inoctets,8,*",
            "CDEF:outbits=outoctets,8,*",
            "COMMENT:\\n",
            "GPRINT:inbits:AVERAGE:Avg In traffic\: %6.2lf %Sbps",
            "COMMENT:  ",
            "GPRINT:inbits:MAX:Max In traffic\: %6.2lf %Sbps\\r",
            "GPRINT:outbits:AVERAGE:Avg Out traffic\: %6.2lf %Sbps",
            "COMMENT: ",
            "GPRINT:outbits:MAX:Max Out traffic\: %6.2lf %Sbps\\r")

    line = sys.stdin.readline()
