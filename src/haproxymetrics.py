import itertools
from prometheus_client import Counter, Histogram, start_http_server

class haproxyLogParser:
    def __init__(self, port, ip=None):
        self.ip = ip
        self.port = port
        self.timer_logs = None
        self.queue_logs = None
        self.backend_server_logs = None
        self.instance_name = []
        self.frontend_http_requests_total = None
        self.backend_http_response_total = None
        self.request_time = None
        self.session_duration = None
        self.request_wait = None
        self.server_tcp_connection_establish = None
        self.request_queued = None
        self.response_processing = None
        self.frontend_byte_read_total = None
        self.backend_byte_read_total = None
        self.backend_queue_length = None
        self.DEFAULT_TIMER_BUCKETS = (
            5,
            10,
            25,
            50,
            75,
            100,
            250,
            500,
            750,
            1000,
            2500,
            5000,
            7500,
            10000,
            float("inf"),
        )
        self.DEFAULT_QUEUE_LENGTH_BUCKETS = tuple(
            itertools.chain(range(0, 10), (20, 30, 40, 60, 100, float("inf")),)
        )

    def expose(self):
        start_http_server(self.port)

    def metrics(self):
        self.frontend_http_requests_total = Counter(
            "frontend_http_requests_total",
            "Count of total number of requests to the frontend",
            labelnames=["status_code", "frontend_name", "server_name"],
            namespace="HAProxy_logs",
        )
        self.session_duration = Histogram(
            "session_duration",
            "Time between accepting the HTTP request and sending back the HTTP response (Tt in HAProxy)",
            labelnames=["frontend_name", "server_name", "logasap"],
            buckets=self.DEFAULT_TIMER_BUCKETS,
            namespace="HAProxy_logs",
        )
        self.request_time = Histogram(
            "request_time",
            " spent waiting for the client to send the full HTTP request (Tq in HAProxy)",
            labelnames=["frontend_name", "server_name", "request_type"],
            namespace="HAProxy_logs",
        )
        self.frontend_byte_read_total = Counter(
            "frontend_bytes_read_total",
            "Total bytes read",
            labelnames=["frontend_name", "server_name"],
            namespace="HAProxy_logs",
        )
        self.backend_queue_length = Histogram(
            "backend_queue_length",
            "Requests processed before this one in the backend queue",
            buckets=self.DEFAULT_QUEUE_LENGTH_BUCKETS,
            labelnames=["frontend_name", "server_name"],
            namespace="HAProxy_logs",
        )
        self.server_queue_length = Histogram(
            "server_queue_length",
            "Length of the server queue when the request was received",
            buckets=self.DEFAULT_QUEUE_LENGTH_BUCKETS,
            labelnames=["frontend_name", "server_name"],
            namespace="HAProxy_logs",
        )
    def set_attribute(self, line):
        self.timer_logs = line[4].split("/")
        self.queue_logs = line[11].split("/")
        self.backend_server_logs = line[3].split("/")
        self.instance_name = self.backend_server_logs[1].split("_")
        if len(self.instance_name) > 1:
            line[2] = line[2] + '_' + self.instance_name[1]
        self.instance_name[-2] = '-'.join(self.instance_name[-2].split("-")[0:-4])
        self.backend_server_logs[1] = self.instance_name[-2] + '_' + self.instance_name[-1]

    def get_attributes(self, line, attr):
        if attr == "frontend_name":
            return line[2]
        elif attr == "status_code":
            return line[5]
        elif attr == "server_name":
            return self.backend_server_logs[1]
        elif attr == "total_time":
            return self.timer_logs[4]
        elif attr == "time_wait_request":
            return self.timer_logs[0]
        elif attr == "time_wait_queues":
            return self.timer_logs[1]
        elif attr == "time_connect_server":
            return self.timer_logs[2]
        elif attr == "time_wait_response":
            return self.timer_logs[3]
        elif attr == "queue_backend":
            return self.queue_logs[1]
        elif attr == "queue_server":
            return self.queue_logs[0]

    def timerMetrics(self, line):
        frontend_name = self.get_attributes(line, "frontend_name")
        server_name = self.get_attributes(line, "server_name")

        def Tt():
            raw_value = self.get_attributes(line, "total_time")

            if raw_value.startswith("+"):
                value = float(raw_value[1:])
                logasap = True
                self.session_duration.labels(
                    logasap=logasap,
                    frontend_name=frontend_name,
                    server_name=server_name,
                ).observe(value)
            else:
                logasap = False
                self.session_duration.labels(
                    logasap=logasap,
                    frontend_name=frontend_name,
                    server_name=server_name,
                ).observe(float(raw_value))
        Tt()
        # TODO: ABORT COUNTER
        timer_metrics = ["time_wait_request", "time_wait_queues", "time_connect_server", "time_wait_response"]
        for metric in timer_metrics:
            value = float(self.get_attributes(line, metric))
            if value != -1:
                self.request_time.labels(
                    frontend_name=frontend_name,
                    server_name=server_name,
                    request_type=metric
                ).observe(value)

    def queueLength(self, line):
        frontend_name = self.get_attributes(line, "frontend_name")
        server_name = self.get_attributes(line, "server_name")

        self.backend_queue_length.labels(
            frontend_name=frontend_name, server_name=server_name
        ).observe(float(self.get_attributes(line, "queue_backend")))
        self.server_queue_length.labels(
            frontend_name=frontend_name, server_name=server_name
        ).observe(float(self.get_attributes(line, "queue_server")))

    def readBytes(self, line):
        self.frontend_byte_read_total.labels(
            frontend_name=self.get_attributes(line, "frontend_name"),
            server_name=self.get_attributes(line, "server_name")
        ).inc()

    def responseRequest(self, line):
        if int(self.get_attributes(line, "status_code")) != -1:
            self.frontend_http_requests_total.labels(
                status_code=self.get_attributes(line, "status_code"),
                frontend_name=self.get_attributes(line, "frontend_name"),
                server_name=self.get_attributes(line, "server_name")
            ).inc()

    def run(self, line):
        self.set_attribute(line)
        self.timerMetrics(line)
        self.queueLength(line)
        self.readBytes(line)
        self.responseRequest(line)

