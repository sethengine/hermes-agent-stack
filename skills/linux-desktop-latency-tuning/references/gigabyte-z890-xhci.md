# Gigabyte Z890 AERO G — xHCI Resume Issue

## Symptom
After S3 sleep/wake, USB input has massive latency (multiple seconds). Journal shows:
```
xhci_hcd 0000:00:0d.0: xHC error in resume, USBSTS 0x401, Reinit
```

## Root Cause
The xHCI controller on the Z890 chipset (Intel 800 Series) has a firmware/handoff issue during S3 resume. USBSTS 0x401 = HCH (Host Controller Halted). The kernel reinitializes the controller, but USB devices re-enumerate during this window, losing their hwdb MOUSE_POLL quirks and usbhid configurations.

## Workarounds

### 1. systemd-sleep hook (best)
See SKILL.md §8 — the resume hook handles this by re-triggering udev for input+usb subsystems after a 2s settle delay.

### 2. BIOS settings to try
- Disable "ERP Ready" (ErP = Energy-Related Products — deep power-off)
- Disable "USB Selective Suspend"
- Set "xHCI Hand-off" to disabled (or enabled — test both)
- Disable "Fast Boot" (skips full USB init)

### 3. s2idle instead of S3
```bash
sudo systemctl edit sleep.target
# Add: SUSPEND_MODE=s2idle
```
s2idle doesn't power off the USB controller root hub — avoids the resume issue entirely. Trade-off: slightly higher idle power.

### 4. PCIe MSI quirk
```bash
pci=nomsi
```
Disables MSI interrupts for PCIe devices. Can fix xHCI interrupt delivery after resume but may affect other devices.

## Known Good Config
- BIOS: F17f
- Kernel: 7.0.x (later 6.x+)
- nvidia-resume.service must complete before USB re-probe
- The 2s `sleep` in the hook is critical — allows NVIDIA resume + USB enumeration to settle
