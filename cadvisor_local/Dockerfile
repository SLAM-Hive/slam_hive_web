FROM google/cadvisor:v0.31.0

ARG CADVISOR_VERSION=v0.56.2
RUN wget -O /usr/bin/cadvisor \
      "https://github.com/google/cadvisor/releases/download/${CADVISOR_VERSION}/cadvisor-${CADVISOR_VERSION}-linux-amd64" \
    && chmod +x /usr/bin/cadvisor

ENTRYPOINT ["/usr/bin/cadvisor", "-logtostderr"]
