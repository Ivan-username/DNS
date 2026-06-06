FROM alpine:3.20

RUN apk add --no-cache bind bind-tools bash \
    && mkdir -p /etc/bind /var/cache/bind/slave-zones /var/run/named \
    && chown -R named:named /var/cache/bind /var/run/named

EXPOSE 53/tcp 53/udp

CMD ["sh", "-c", "chown -R named:named /var/cache/bind/slave-zones && exec named -f -c /etc/bind/named.conf -u named"]
