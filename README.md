# HaProxy-Log-exporter

## About

- Exposes Metrics like Tw, Tc, Tr, Tt, Tq, backend and frontend queue lengths, request count and corresponding histograms from HAProxy logs

Following time based histograms

| Metric| Meaning  |
| :-----: | :-: |
| TR | The total time to get the client request (HTTP Mode only) |
| Tw | The total time spent in the queues waiting for a connection slot |
| Tc | The total time to establish the TCP connection to the server |
| Tr | The server response time (HTTP mode only) |
| Ta | The total active time for the HTTP reuest (HTTP mode only) |
| Tt | The total TCP session duration time, between the moment the proxy accepted it and the moment both ends were closed 

## Usage
- End Point to Prometheus: Add following lines to the prometheus.yml

 ```shell
  - job_name: haproxy_log
   static_configs:
    - targets:
      - localhost:YOUR_PORT
 ```
- Provide suitable port to run.py (Currently Have to edit file #fix this later)

### To run: 
```
usage: haproxylog.py [-h] [-f LOG_PATH] [-c CONTAINER] [-z CLEANUP] [-v CONFIG] [-g CONTAINER_CONFIG] [-t CLEANUP_TIMER]

HAProxy Log Exporter

optional arguments:
  -h, --help            show this help message and exit
  -f LOG_PATH, --log_path LOG_PATH
                        enter file path
  -c CONTAINER, --container CONTAINER
                        enter docker container
  -z CLEANUP, --cleanup CLEANUP
                        Should clean up or not
  -v CONFIG, --config CONFIG
                        HAProxy config path
  -g CONTAINER_CONFIG, --container_config CONTAINER_CONFIG
                        Path inside container
  -t CLEANUP_TIMER, --cleanup_timer CLEANUP_TIMER
                        Periodic clean up(in min)
```


 ```shell
  - pip install -r requirements.txt
  - python haproxylog.py --container container_id or --log_path log_id --config or --container_config --cleanup_timer --cleanip
 ```

 - Docker

 
 *ADD NOTIFICATION URLS TO flockRequests.PY
```
sudo docker build -t haproxy_log_parser

sudo docker run -it --rm --net host -v /var/lib/docker/containers/:/src/mount/haproxylog -v /var/lib/docker/overlay2/:/src/mount/dcos-app-proxy -e DCOS_HAPROXY_CONTAINER="'"$(sudo docker ps -q --filter ancestor=$IMAGE_NAME)"'" haproxy_log_parser /src/docker_entrypoint.sh  --cleanup_timer 1 --config $(sudo docker inspect --format='{{json .GraphDriver}}' $(sudo docker ps -q --filter ancestor=$IMAGE_NAME)) --cleanup 1

 ```
 *replace IMAGE_NAME




