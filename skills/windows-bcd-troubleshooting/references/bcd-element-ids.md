# BCD element IDs (authoritative map)

Source: Geoff Chappell — https://geoffchappell.com/notes/windows/boot/bcd/elements.htm
(~62K chars; when extracting, raise char_limit ≥ 70000 or grep the web_extract cache at ~/.hermes/cache/web/ — the default 15K truncates the middle where the OS-loader timer elements live.)

## Element datatype encoding
- `0xF0000000` class: 1 = library, 2 = application, 3 = device, 4 = template
- `0x0F000000` format: 1 = device, 2 = string, 3 = GUID, 4 = GUID list, 5 = integer, 6 = boolean, 7 = integer list
- e.g. `0x260000A2`: class 2 (application) + format 6 (boolean) → OS-loader boolean.

## Boot Manager (object {9dea862c-5cdd-4e70-acc1-f32b344d4795})
- `0x24000001` displayorder (GUID list)
- `0x23000003` **default** (GUID) — the default OS entry
- `0x25000004` timeout (integer)
- `0x26000005` resume (boolean); `0x23000006` resumeobject (GUID)

## OSLoader — timers & perf (the ones that matter)
| ID | Friendly name | Format / values |
|---|---|---|
| `0x260000A2` | **useplatformclock** | boolean — forces HPET when true. THE harmful one. |
| `0x250000A6` | **tscsyncpolicy** | integer: 0 = Default, 1 = Legacy, 2 = Enhanced |
| `0x260000A4` | **useplatformtick** | boolean |
| `0x260000A5` | **disabledynamictick** | boolean |
| `0x25000020` | nx | integer: 0 = OptIn, 1 = OptOut, 2 = AlwaysOff, 3 = AlwaysOn |
| `0x250000C2` | bootmenupolicy | integer: 0 = Legacy, 1 = Standard |
| `0x25000055` | x2apicpolicy | integer: 0 = Default, 1 = Disable, 2 = Enable |
| `0x25000070` | usefirmwarepcisettings | boolean (WMI symbol historically misnamed integer) |

**Wrong-ID gotchas (commonly mis-cited on forums/guides):**
- `useplatformclock` is `0x260000A2`, NOT `0x25000090`.
- `tscsyncpolicy` is `0x250000A6`, NOT `0x250000c3`.

## OSLoader — identity/basics
- `0x21000001` osdevice (device)
- `0x22000002` systemroot (string)
- `0x23000003` resumeobject (GUID → the resume entry; normal)
- `0x25000008` (integer, 1809+)

## Library — identify any object
- `0x12000002` application path (e.g. `\WINDOWS\system32\winload.efi`)
- `0x12000004` description ("Windows 11", "Windows Resume Application", …)
- `0x12000005` locale (e.g. en-GB)
- `0x14000006` inherit (GUID list); `0x14000008` recoverysequence (GUID list)

## Reading values
```
hivexget <BCD> 'Objects\{<guid>}\Elements\260000A2' 'Element'
```
- Boolean true prints as escaped binary `\u0001...`; integer 0 prints as 8 zero bytes. Compare raw bytes.
- Enumerate an object's elements:
  ```
  printf 'cd Objects\\{<guid>}\\Elements\nls\nquit\n' | hivexsh <BCD>
  ```
