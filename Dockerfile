FROM registry.fedoraproject.org/fedora:35
COPY requirements.txt notify.py /
COPY thetagang_notifications /thetagang_notifications
ENV PYTHONUNBUFFERED=1
RUN dnf -y install python && dnf clean all
RUN curl -s https://bootstrap.pypa.io/get-pip.py | python
RUN pip3 install -r /requirements.txt
CMD ["/notify.py"]
