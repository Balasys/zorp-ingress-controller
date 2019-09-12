# Copyright 2019 Balasys
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#FROM micado/zorpgpl:6.0.12
FROM balasys/zorpgpl:latest

#RUN echo 'Acquire::AllowInsecureRepositories "1";' > /etc/apt/apt.conf.d/98zorp
RUN apt-get update && apt-get -y install --no-install-recommends wget python3-setuptools && rm -rf /var/lib/apt/lists/*
RUN easy_install3 pip
COPY /fs /
COPY /zorp_ic /zorp_ic
ARG DUMB_INIT_SHA256=37f2c1f0372a45554f1b89924fbb134fc24c3756efaedf11e07f599494e0eff9
RUN wget --no-check-certificate -O /dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.2/dumb-init_1.2.2_amd64 && \
    echo "$DUMB_INIT_SHA256  /dumb-init" | sha256sum -c -
COPY build/requirements.txt /tmp/requirements.txt

RUN pip3 install --upgrade setuptools urllib3 chardet requests
RUN pip3 install --upgrade -r /tmp/requirements.txt && rm /tmp/requirements.txt
#RUN pip3 install kubernetes

RUN chmod +x /dumb-init && \
    chmod +x /etc/init.d/zorp

ENTRYPOINT ["/dumb-init", "--", "/start.sh"]
