import subprocess
from collections import defaultdict
from pyhaproxy.parse import Parser
from prometheus_client import REGISTRY

def getConfig(container, container_config):
    subprocess.run(["docker", "cp", str(container)+':'+ str(container_config), 'haproxy.cfg'])
    return 'haproxy.cfg'

def getRegApps(metric_names):
    regApps = defaultdict(list)
    for metric in REGISTRY.collect():
        for sample in metric.samples:
            for local_metric in metric_names:
                if local_metric in sample.name:
                    regApps[local_metric].append(sample.labels)
    return regApps

def getCurrApps(config_path):
    currApps = []
    cfg_parser = Parser(config_path)
    configuration = cfg_parser.build_configuration()
    for backend in configuration.backends:
        for server in backend.servers():
            instance_name = server.name.split("_")
            instance_name[-2] = '-'.join(instance_name[-2].split("-")[0:-4])
            server.name = instance_name[-2] + '_' + instance_name[-1]
            currApps.append(server.name)
    return currApps

def removeStaleMetrics(metrics_list, metric_names, config_in_docker=False, config_path=None, container=None, container_config=None):
    if config_in_docker:
        config_path = getConfig(container, container_config)
    currApps = getCurrApps(config_path)
    regApps = getRegApps(metric_names)
    for metric in metrics_list:
        name = metric.describe()[0].name
        labels = regApps[name]
        for label in labels:
            if 'server_name' in label:
                if label['server_name'] not in currApps:
                    args = []
                    if "status_code" in label:
                        args.append(label['status_code'])   
                    if "frontend_name" in label:
                        args.append(label['frontend_name'])                                                
                    args.append(label['server_name'])
                    if "request_type" in label:
                        args.append(label['request_type'])              
                    if "logasap" in label:
                        args.append(label['logasap'])     
                    try:       
                        metric.remove(*args)
                        print(label['server_name'])                
                    except Exception as e:
                        print(e)
