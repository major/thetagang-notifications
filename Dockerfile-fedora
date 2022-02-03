FROM registry.fedoraproject.org/fedora:35
RUN echo "fastestmirror=1" >> /etc/dnf/dnf.conf
RUN dnf -y upgrade && dnf -y install python && dnf clean all
RUN curl -s https://bootstrap.pypa.io/get-pip.py | python
COPY requirements.txt notify.py /
COPY thetagang_notifications /thetagang_notifications
ENV PYTHONUNBUFFERED=1
RUN pip3 install -r /requirements.txt
CMD ["/notify.py"]
