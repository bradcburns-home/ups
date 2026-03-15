FROM debian:11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       nut-server \
       nut-client \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/nut \
    && chown nut:nut /run/nut

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY nut-notify.sh /usr/local/bin/nut-notify.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/nut-notify.sh

EXPOSE 3493

ENTRYPOINT ["entrypoint.sh"]
