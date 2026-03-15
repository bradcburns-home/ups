#!/bin/bash
set -e

mkdir -p /run/nut

# On boot, the kernel usbhid driver claims the UPS before this container starts.
# Unbind it via sysfs so NUT's usbhid-ups can claim the device instead.
for iface in /sys/bus/usb/drivers/usbhid/[0-9]*; do
    [ -e "$iface" ] || continue
    dev_path="${iface%:*}"
    if [ -f "$dev_path/idVendor" ] && [ "$(cat "$dev_path/idVendor")" = "0463" ]; then
        echo "Unbinding kernel usbhid from $(basename "$iface")"
        echo -n "$(basename "$iface")" > /sys/bus/usb/drivers/usbhid/unbind 2>&1 || true
    fi
done

echo "Starting UPS driver..."
upsdrvctl -u root start

echo "Starting upsd in foreground..."
upsd -D -u root &
UPSD_PID=$!

sleep 2

echo "Starting upsmon..."
upsmon -u root

wait $UPSD_PID
