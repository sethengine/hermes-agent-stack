# KDE Wayland Mouse Acceleration via DBus

## Why DBus?
`libinput list-devices` shows **libinput library defaults**, NOT what the compositor (KWin) is actually using. The real acceleration profile is set by KWin's libinput context and exposed via DBus.

## Find Your Mouse's DBus Path
Event numbers change on replug/logout. Always re-find:
```bash
for ev in event0 event1 event2 event3 event4 event5 event6 event7 event8 event9 event10 event11 event12 event13 event14 event15 event16 event17 event18 event19 event20 event21; do
    NAME=$(dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/$ev org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"name" 2>&1 | grep -o '"Corsair.*"' | tr -d '"')
    if [ -n "$NAME" ]; then
        PTR=$(dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/$ev org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"pointer" 2>&1 | grep -c "true")
        ACCEL=$(dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/$ev org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"pointerAcceleration" 2>&1 | grep double | tr -s ' ' | cut -d' ' -f4)
        FLAT=$(dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/$ev org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"pointerAccelerationProfileFlat" 2>&1 | grep -c "true")
        echo "$ev: $NAME pointer=$PTR accel=$ACCEL flat=$FLAT"
    fi
done
```

## Check Current Profile
```bash
DEV=event3  # replace with your found event number
dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/$DEV \
  org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"pointerAccelerationProfileFlat"

dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/$DEV \
  org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"pointerAccelerationProfileAdaptive"

dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/$DEV \
  org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"pointerAcceleration"
```

## Set Flat Profile (No Logout Needed)
```bash
DBUS="dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/event3 org.freedesktop.DBus.Properties.Set string:org.kde.KWin.InputDevice"

$DBUS string:pointerAccelerationProfileFlat variant:boolean:true
$DBUS string:pointerAccelerationProfileAdaptive variant:boolean:false
$DBUS string:pointerAcceleration variant:double:0.0
```

## Available Properties on KWin InputDevice
Read/Write:
  - pointerAccelerationProfileFlat (boolean)
  - pointerAccelerationProfileAdaptive (boolean)
  - pointerAcceleration (double)
  - outputName (string)
  - enabled (boolean)
  - leftHanded (boolean)

Read-only (defaults):
  - defaultPointerAccelerationProfileFlat
  - defaultPointerAccelerationProfileAdaptive
  - defaultPointerAcceleration
  - supportsPointerAcceleration
  - supportsPointerAccelerationProfileFlat

## Known Warnings
- Setting via DBus may be overridden by KDE's System Settings GUI at next login
- The kcminputrc per-device section can reset profile on next session
- KDE 6 Wayland: `kquitapp5 kcminit && kstart5 kcminit` may not reload libinput context
