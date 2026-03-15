#!/bin/sh
# NOTIFYCMD handler — emits structured JSON to PID 1's stdout for Docker logging.
# $NOTIFYTYPE and $UPSNAME are set by upsmon.
SEV="WARNING"
case "$NOTIFYTYPE" in ONLINE|COMMOK) SEV="INFO" ;; esac

printf '{"severity":"%s","message":"%s","source":"nut","service":"upsmon","event":"%s","ups":"%s"}\n' \
  "$SEV" "$*" "$NOTIFYTYPE" "$UPSNAME" \
  > /proc/1/fd/1 2>/proc/1/fd/2
