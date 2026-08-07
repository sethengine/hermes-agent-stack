# Gigabyte WMI Method Table

Decompiled from `_WDG` and `WQCC` tables (originally shared in [t-8ch/linux-gigabyte-wmi-driver#10](https://github.com/t-8ch/linux-gigabyte-wmi-driver/issues/10)).

## WMI Device Map

| GUID | Object | Flags | Purpose |
|------|--------|-------|---------|
| `DEADBEEF-1000-0000-00A0-C90629100000` | AA | `ACPI_WMI_EXPENSIVE` (0x1) | Data block — sensor data store |
| `DEADBEEF-2001-0000-00A0-C90629100000` | BB | `ACPI_WMI_METHOD` (0x2) | Method interface — callable commands |
| `DEADBEEF-4002-0000-00A0-C90629100000` | — | `ACPI_WMI_EVENT` (0x8) | Event — broadcast/notification |
| `05901221-D566-11D1-B2F0-00A0C9062910` | CC | 0 | WMI BMOF (metadata) |

## Method Command IDs (via `DEADBEEF-2001` / `WQBB->GSA1_ACPIMethod`)

Passed as the second argument to `wmidev_evaluate_method(wdev, 0x0, command, &in, &out)`.

### System / Info (1-10)

| Cmd | Name | Description |
|-----|------|-------------|
| 1 | `GsaTest` | Self-test |
| 2 | `GsaGetHWIDString` | Get hardware ID |
| 3 | `GsaGetFWTagString` | Get firmware tag |
| 4 | `GsaGetFWVerString` | Get firmware version |
| 5 | `GsaGetHWConfig` | Get hardware config |
| 6 | `GsaGetFlashSize` | Get flash size |
| 7 | `GsaGetCapabilityD0` | Get capability D0 |
| 8 | `GsaGetGSAVersion` | Get GSA version |
| 9 | `EZVGetVersion` | EZV version |
| 10 | (unused) | — |

### I2C (92-96)

| Cmd | Name |
|-----|------|
| 92 | `I2CBaseMemAddr` |
| 93 | `I2CBusTest` |
| 94 | `I2CWriteRead` |
| 95 | `I2CWriteReadBlock` |
| 96 | (unused) |

### SMBus (97-109)

| Cmd | Name |
|-----|------|
| 97 | `SMBBaseAddr` |
| 98 | `SMBQuickWrite` |
| 99 | `SMBQuickRead` |
| 100 | `SMBSendByte` |
| 101 | `SMBReceiveByte` |
| 102 | `SMBWriteByte` |
| 103 | `SMBReadByte` |
| 104 | `SMBWriteWord` |
| 105 | `SMBReadWord` |
| 106 | `SMBBlockWrite` |
| 107 | `SMBBlockRead` |
| 108 | `SMBBlockWriteE32B` |
| 109 | (unused) |

### PIO (110-115)

| Cmd | Name |
|-----|------|
| 110 | `PIORead8` |
| 111 | `PIOWrite8` |
| 112 | `PIORead16` |
| 113 | `PIOWrite16` |
| 114 | `PIORead32` |
| 115 | `PIOWrite32` |

### PCI (120-128)

| Cmd | Name |
|-----|------|
| 120 | `PCIGetPcieMmioBaseAddr` |
| 121 | `PCIRead8` |
| 122 | `PCIWrite8` |
| 123 | `PCIRead16` |
| 124 | `PCIWrite16` |
| 125 | `PCIRead32` |
| 126 | `PCIWrite32` |
| 127 | `PCIRead32Bits` |
| 128 | `PCIWrite32Bits` |

### Memory (130-139)

| Cmd | Name |
|-----|------|
| 130 | `MEMRead8` |
| 131 | `MEMWrite8` |
| 132 | `MEMRead16` |
| 133 | `MEMWrite16` |
| 134 | `MEMRead32` |
| 135 | `MEMWrite32` |
| 136 | `MEMRead32Bits` |
| 137 | `MEMWrite32Bits` |
| 138 | `MEMRead32Buffer` |
| 139 | `MEMWrite32Buffer` |

### Broadcast (190)

| Cmd | Name |
|-----|------|
| 190 | `BROADCAST_SendEvent` |

### EZV Voltage (280-289, 1000) ⚡

| Cmd | Name | Description |
|-----|------|-------------|
| **280** | **`EZVGetVoltage`** | **Read a voltage rail** |
| 281 | `EZVSetVoltage` | Set a voltage rail |
| 282 | `EZVGetHwId` | Get hardware ID of a voltage rail |
| 283 | `EZVHwValue2ItemValue` | Convert HW value → UI value |
| 284 | `EZVItemValue2HwValue` | Convert UI value → HW value |
| 285 | `EZVGetUIInfo` | Get voltage UI info |
| 286 | `EZVHwValue2ItemStr` | HW value → display string |
| 287 | `EZVItemStr2HwValue` | Display string → HW value |
| 288 | `EZVGetItem` | Get voltage item/rail info |
| 289 | `EZVSetItem` | Set voltage item/rail |
| 1000 | `EZVAAA` | Unknown |

### ZFC Fan Control (290-299) 🌡️

| Cmd | Name | Description |
|-----|------|-------------|
| 290 | `ZFCGetHwId` | Get fan controller HW ID |
| 291 | `ZFCGetFanStopStatus` | Check if fan is stopped |
| 292 | `ZFCSetFanStopStatus` | Set fan stop status |
| **293** | **`ZFCGetCurrentTemp`** | **Read temperature sensor** (used by gigabyte-wmi) |
| 294 | `ZFCSetVirtualTemp` | Set virtual temperature |
| 295 | `ZFCGetFanTargetTemp` | Get fan target temperature |
| 296 | `ZFCSetFanTargetTemp` | Set fan target temperature |
| 297 | `ZFCGetFanTempLimit` | Get fan temperature limit |
| 298 | `ZFCSetFanTempLimit` | Set fan temperature limit |
| 299 | `ZFCFanOnOff` | Fan on/off control |

### DDR (300, 310)

| Cmd | Name |
|-----|------|
| 300 | `DDRGetCapable` |
| 310 | `DDRGetSpdData` |

### IOT (320-322)

| Cmd | Name |
|-----|------|
| 320 | `IotPinMode` |
| 321 | `IotDigitalWrite` |
| 322 | `IotDigitalRead` |

### PD (325-332)

| Cmd | Name |
|-----|------|
| 325 | `PDGetStatus` |
| 326 | `PDSetStatus` |
| 327 | `PDGetHwId` |
| 328 | `PDGetPortInfo` |
| 329 | `PDGetPortCount` |
| 330 | `PDSetMode` |
| 331 | `PDGetMode` |
| 332 | `PDOffOn` |

### OPB (335-336)

| Cmd | Name |
|-----|------|
| 335 | `OPBEnable` |
| 336 | `OPBGetHwId` |

### ETB (230-233)

| Cmd | Name |
|-----|------|
| 230 | `ETBEnable` |
| 231 | `ETBGetMode` |
| 232 | `ETBSetMode` |
| 233 | `ETBGetHwId` |

### USW (240-242)

| Cmd | Name |
|-----|------|
| 240 | `USWGetStatus` |
| 241 | `USWSetStatus` |
| 242 | `USWGetHwId` |

### NCT (250-252)

| Cmd | Name |
|-----|------|
| 250 | `NCTGetChipInfo` |
| 251 | `NCTGetVRFReg` |
| 252 | `NCTSetVRFReg` |

### ADJ (220-221)

| Cmd | Name |
|-----|------|
| 220 | `ADJGetStage` |
| 221 | `ADJGetHwId` |

## Usage Notes

- `ZFCGetCurrentTemp` (cmd 293 = 0x125) is what the existing `gigabyte-wmi` driver calls with the sensor index in `arg1`.
- `EZVGetVoltage` (cmd 280 = 0x118) is available but **not implemented** by the current in-kernel driver — a driver patch would be needed to expose voltages via hwmon.
- The data block at `DEADBEEF-1000` (object AA) is NOT a callable method — it's a data store with "expensive" flag, meaning reads take measurable time.
- Event at `DEADBEEF-4002` (notify 0xE2) is the broadcast event channel.
