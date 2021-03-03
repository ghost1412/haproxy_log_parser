import os, glob
import sys
import time
import ujson
import tailhead
import argparse
import subprocess
from haproxymetrics import haproxyLogParser
from cleaner import removeStaleMetrics
from helper.repeatedTimer import RepeatedTimer
from helper.flockRequests import error_report

h = haproxyLogParser(8001)

h.expose()
h.metrics()

parser = argparse.ArgumentParser(description='HAProxy Log Exporter')
parser.add_argument('-f', '--log_path', action='store', help='enter file path', default=None)
parser.add_argument('-c', '--container', action='store', help='enter docker container', default=None)
parser.add_argument('-z', '--cleanup', action='store', help='Should clean up or not', default=int(0))
parser.add_argument('-v', '--config', action='store', help='HAProxy config path', default=None)
parser.add_argument('-g', '--container_config', action='store', help='Path inside container', default=None)
parser.add_argument('-t', '--cleanup_timer', action='store', help='Periodic clean up(in min)', default=None)
parsed = parser.parse_args()

container = parsed.container

if container:
    path = subprocess.run(["docker", "inspect", "--format='{{.LogPath}}'", str(container)], stdout=subprocess.PIPE).stdout.decode("utf-8").rstrip()[1:-1]
elif 'DCOS_HAPROXY_CONTAINER' in os.environ:
    container = os.environ.get('DCOS_HAPROXY_CONTAINER')
    path = glob.glob("/src/mount/haproxylog/{}*".format(container).replace("'", ""))
    config_uuid = ujson.loads(parsed.config)['Data']['MergedDir'].split('/')[-2]
    config = glob.glob('/src/mount/dcos-app-proxy/{}*/merged/app/'.format(config_uuid).replace("'", "") + 'haproxy.cfg')[0]
    if len(path) > 1:
        error_report("Contains more than 1 container with similar name")
    elif len(path) == 0:
        error_report("No container for the image")
    else:
        path = path[0] + '/' + path[0].split('/')[-1] + '-json.log'
else:
    path = parsed.log_path

isCleanUp = int(parsed.cleanup)

container_config = parsed.container_config

timer = int(parsed.cleanup_timer)

if path is None:
    print("Enter Log Path or Docker container")
    exit()

def collect_process_logs():
    for raw_line in tailhead.follow_path(path):
        print(raw_line)
        if raw_line is None:
            time.sleep(0.1)
            continue
        try:
            raw_line = ujson.loads(raw_line)
            line = str(raw_line["log"])
            if 'GET' not in line:
                continue
            h.run(line.split())
        except Exception as e:
            error_report(str(e))
            continue

if __name__ == "__main__":  
    if isCleanUp:
        metric_list = [h.frontend_byte_read_total,
                    h.frontend_http_requests_total,
                    h.request_time,
                    h.session_duration,
                    h.backend_queue_length,
                    h.server_queue_length]
        metric_name = []
        for metric in metric_list:
            metric_name.append(metric.describe()[0].name)
        if container_config is None:
            cleanup_job = RepeatedTimer(60*timer, removeStaleMetrics, metric_list, metric_name, config_path=config)
        else:
            cleanup_job = RepeatedTimer(60*timer, removeStaleMetrics, metric_list, metric_name, config_in_docker=True, container=container, container_config=container_config)
    while True:
        try:     
            collect_process_logs()
        except Exception as e:
            error_report(str(e))
            h.expose()
            h.metrics()

