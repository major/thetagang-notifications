FROM docker.io/library/python:3.10
COPY requirements.txt /
RUN pip install -U pip -r /requirements.txt
COPY notify.py /
COPY thetagang_notifications /thetagang_notifications
ENV PYTHONUNBUFFERED=1
CMD ["/notify.py"]
