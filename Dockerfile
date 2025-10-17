FROM python:3.11-alpine as builder
RUN apk --update add bash nano g++
COPY ./requirements.txt /vampi/requirements.txt
WORKDIR /vampi
RUN pip install -r requirements.txt

# Build a fresh container, copying across files & compiled parts
FROM python:3.11-alpine
RUN apk --update add bash curl
COPY . /vampi
WORKDIR /vampi
COPY --from=builder /usr/local/lib /usr/local/lib
COPY --from=builder /usr/local/bin /usr/local/bin

# Environment variables
ENV vulnerable=1
ENV tokentimetolive=60
ENV BOOTSTRAP_USERS=50
ENV BOOTSTRAP_BOOKS_PER_USER=5

# Make bootstrap script executable
RUN chmod +x /vampi/tools/bootstrap.py

ENTRYPOINT ["python"]
CMD ["app.py"]
