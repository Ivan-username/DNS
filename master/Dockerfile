FROM alpine:3.20

RUN apk add --no-cache bind bind-tools bash \
    && mkdir -p /etc/bind/zones /var/cache/bind /var/run/named /var/log/bind \
    && chown -R named:named /var/cache/bind /var/run/named /var/log/bind

EXPOSE 53/tcp 53/udp 953/tcp

CMD ["named", "-f", "-c", "/etc/bind/named.conf", "-u", "named"]
