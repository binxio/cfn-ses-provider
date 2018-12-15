FROM python:3.6
RUN apt-get update && apt-get install -y zip
WORKDIR /lambda

ADD requirements.txt /tmp
RUN pip install --quiet -t /lambda -r /tmp/requirements.txt

ADD src/ /lambda/
RUN python -m compileall -q /lambda

RUN find /lambda -type d | xargs -I {} chmod ugo+rx "{}" && \
    find /lambda -type f | xargs -I {} chmod ugo+r "{}"


ARG ZIPFILE=lambda.zip
RUN zip --quiet -9r /${ZIPFILE}  .

FROM scratch
ARG ZIPFILE
COPY --from=0 /${ZIPFILE} /
