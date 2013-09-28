#!/usr/bin/env python
import sys
import yaml
import re
import os
import rrdtool
import logging as log

TARGET_DIRECTORY = '/tmp/'
step = 300
heartbeat = step * 2


def update_traffic_database(filename, traffic_in, traffic_out):
    # Update the file with the new data
    ret = rrdtool.update(filename,
        'N:' + str(traffic_in) + ':' + str(traffic_out))
    if ret:
        print rrdtool.error()


def verify_traffic_database_file(filename):
    # If we have no data file for this ip, create one
    if not os.path.exists(filename):
        log.info('Creating new data file for %s', ip)
        rrdtool.create(filename,
            "--step", str(step), "--start", "0",
            "DS:input:COUNTER:%s:U:U" % str(heartbeat),
            "DS:output:COUNTER:%s:U:U" % str(heartbeat),
            "RRA:AVERAGE:0.5:1:600",
            "RRA:AVERAGE:0.5:12:240",
            "RRA:AVERAGE:0.5:288:70",
            "RRA:AVERAGE:0.5:2016:70",
            "RRA:AVERAGE:0.5:60480:120",
            "RRA:MAX:0.5:12:240",
            "RRA:MAX:0.5:288:70",
            "RRA:MAX:0.5:2016:300",
            "RRA:MAX:0.5:60480:120",
            )


def graph_traffic_for_ip(filename, duration='1h'):
    in_area_color = '0018CDbb'
    in_line_color = 'A0A0A0ff'
    out_area_color = '8F480099'
    out_line_color = 'a05050a0'
    over_line_color = '00FF0099'
    rrdtool.graph(filename.replace('.rrd', '.png'),
        '--imgformat', 'PNG',
        '--width', '540',
        '--height', '150',
        '--start', "end-" + duration,
        '--end', "now",
        '--vertical-label', 'Bytes/Second',
        '--title', 'Traffic for %s' % ip,
        '--lower-limit', '0',
        '--color', 'BACK#F0F0D000', '--color', 'CANVAS#F0F0D000',
        '--color', 'SHADEA#F0F0D000', '--color', 'SHADEB#F0F0D000',
        '--color', 'GRID#E0E0E0AA',
        'DEF:in_bytes=%s:input:AVERAGE' % filename,
        'DEF:out_bytes=%s:output:AVERAGE' % filename,
        'CDEF:in_mb=in_bytes,1,/',
        'AREA:in_mb#%s:Download' % in_area_color,
        'LINE1:in_mb#%s' % in_line_color,
        'HRULE:10000#%s' % over_line_color,
        'CDEF:out_mb=out_bytes,1,/',
        'AREA:out_mb#%s:Upload' % out_area_color,
        'LINE1:out_mb#%s' % out_line_color,
        "COMMENT:\\n",
        "GPRINT:in_mb:AVERAGE:Avg In traffic\: %6.2lf MBps",
        "COMMENT:  ",
        "GPRINT:in_mb:MAX:Max In traffic\: %6.2lf MBps\\r",
        "GPRINT:out_mb:AVERAGE:Avg Out traffic\: %6.2lf MBps",
        "COMMENT: ",
        "GPRINT:out_mb:MAX:Max Out traffic\: %6.2lf MBps\\r")


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
        filename = os.path.join(TARGET_DIRECTORY, ip + '.rrd')

        verify_traffic_database_file(filename)

        update_traffic_database(filename, traffic_in, traffic_out)

        graph_traffic_for_ip(filename)

    # Get next line
    line = sys.stdin.readline()

# Generate index page
template_name = 'ip_traffic.jinja'
target_index = 'ip_traffic.html'
import os
import jinja2
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

ip_list = []
for filename in os.listdir(TARGET_DIRECTORY):
    if filename.endswith('.png'):
        ip_list.append(os.path.splitext(filename)[0])

template = jinja_environment.get_template(template_name)
context = {
        'ips': ip_list,
        'dir': TARGET_DIRECTORY,
    }
content = template.render(context)
index_file = open(os.path.join(TARGET_DIRECTORY, target_index), 'w')
index_file.write(content)
index_file.close()
