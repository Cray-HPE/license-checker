FROM python:latest
RUN pip3 install requests pyyaml
COPY license_check.py license_check.yaml /
WORKDIR /github/workspace
ENTRYPOINT ["/usr/local/bin/python3", "/license_check.py"]