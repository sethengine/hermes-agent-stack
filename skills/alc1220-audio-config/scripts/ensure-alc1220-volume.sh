#!/usr/bin/env bash
# Retry fixing alc1220 headphone volume until the device is initialized
# Runs from PipeWire context.exec on every startup.
# Retries up to 10 seconds because the adapter opens hw:1 AFTER context.exec runs.
for i in $(seq 1 10); do
    /usr/bin/amixer -c1 cset numid=3 87,87 2>/dev/null && \
    /usr/bin/amixer -c1 cset numid=4 on,on 2>/dev/null
    STATUS=$?
    if [ "$STATUS" = 0 ] && [ "$(/usr/bin/amixer -c1 cget numid=3 2>/dev/null | grep -c 'values=87,87')" -gt 0 ]; then
        exit 0
    fi
    sleep 1
done
exit 1
