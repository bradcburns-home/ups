FROM debian:12-slim AS build

ARG NUT_VERSION=2.8.3

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gcc g++ make autoconf automake libtool pkg-config \
    libusb-1.0-0-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://github.com/networkupstools/nut/releases/download/v${NUT_VERSION}/nut-${NUT_VERSION}.tar.gz" \
    -o /tmp/nut.tar.gz \
    && tar -xzf /tmp/nut.tar.gz -C /tmp

RUN cd /tmp/nut-${NUT_VERSION} && \
    ./configure \
        --prefix=/usr \
        --sysconfdir=/etc/nut \
        --with-statepath=/var/run/nut \
        --with-altpidpath=/var/run/nut \
        --with-pidpath=/var/run/nut \
        --with-drvpath=/usr/lib/nut \
        --with-user=nut \
        --with-group=nut \
        --with-usb \
        --with-ssl=openssl \
        --without-cgi \
        --without-dev \
        --without-doc \
        --without-neon \
        --without-snmp \
        --without-powerman \
        --without-ipmi \
        --without-modbus \
        --without-avahi \
        --without-wrap \
        --disable-static \
    && make -j"$(nproc)" \
    && make install DESTDIR=/nut-install

FROM debian:12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libusb-1.0-0 libssl3 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r nut \
    && useradd -r -g nut -d /var/run/nut -s /usr/sbin/nologin nut \
    && mkdir -p /var/run/nut \
    && chown nut:nut /var/run/nut

COPY --from=build /nut-install/usr/ /usr/
COPY --from=build /nut-install/etc/ /etc/

RUN ldconfig

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY nut-notify.sh /usr/local/bin/nut-notify.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/nut-notify.sh

EXPOSE 3493

ENTRYPOINT ["entrypoint.sh"]
