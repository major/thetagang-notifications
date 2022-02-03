FROM docker.io/library/python:3.10
COPY requirements.txt notify.py /
COPY thetagang_notifications /thetagang_notifications
ENV PYTHONUNBUFFERED=1
RUN curl -s https://bootstrap.pypa.io/get-pip.py | python
RUN pip install --no-cache-dir -r /requirements.txt
CMD ["/notify.py"]
