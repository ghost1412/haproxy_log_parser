FROM python
RUN pip3 install pyhaproxy
RUN pip3 install tailhead
RUN pip3 install prometheus_client
RUN pip3 install ujson


ADD . /var/lib/docker/containers
STOPSIGNAL SIGUSR1
COPY src/ /src/
WORKDIR /src
RUN ls
RUN chmod +x docker_entrypoint.sh
CMD ["sh", "/src/docker-entrypoint.sh", "run"]