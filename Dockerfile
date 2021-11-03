FROM python:latest
RUN pip3 install requests pyyaml
COPY license_check* /license_check/
COPY tests/* /license_check/tests/
RUN groupadd -g 10000 github-actions-runner && \
    useradd -u 10000 -g 10000 github-actions-runner
USER github-actions-runner
RUN /usr/local/bin/python3 /license_check/license_check_test.py
WORKDIR /github/workspace
ENTRYPOINT ["/usr/local/bin/python3", "/license_check/license_check.py"]