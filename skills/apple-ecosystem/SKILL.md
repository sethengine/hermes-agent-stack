---
name: apple-ecosystem
description: "Integrate with the Apple ecosystem on macOS: Notes, Reminders, Find My, iMessage, and desktop automation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Apple, macOS, Notes, Reminders, FindMy, iMessage, Automation, iCloud]
    related_skills: [obsidian]
---

# Apple Ecosystem Integration

Work with Apple services and macOS apps from the terminal. All tools below require macOS and appropriate permissions.

---

## Apple Notes

Use `memo` to manage Apple Notes directly from the terminal. Notes sync across all Apple devices via iCloud.

### Prerequisites

- Install: `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- Grant Automation access to Notes.app when prompted

### Quick Reference

```bash
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes
memo note "Note Title"            # View a specific note
memo create -t "Title" -b "Body text"  # Create a note
memo export -f "Folder" -o ./backup    # Export to Markdown
```

---

## Apple Reminders

Use `remindctl` to manage Apple Reminders. Tasks sync across all Apple devices via iCloud.

### Prerequisites

- Install: `brew install steipete/tap/remindctl`
- Grant Reminders permission when prompted

### Quick Reference

```bash
remindctl                    # Today's reminders
remindctl today              # Same
remindctl list               # All lists
remindctl add "Buy milk" --list Shopping --due "tomorrow 10am"
remindctl complete "Buy milk"
```

---

## Find My

Track Apple devices and AirTags via FindMy.app using AppleScript and screen capture.

### Prerequisites

- macOS with Find My app and iCloud signed in
- Screen Recording permission for terminal (System Settings → Privacy → Screen Recording)
- Optional: `brew install steipete/tap/peekaboo` for better UI automation

### Quick Reference

```bash
# Open FindMy and take a screenshot
osascript -e 'tell application "FindMy" to activate'
sleep 3
screencapture -x findmy.png
```

---

## iMessage

Read and send iMessage/SMS via macOS Messages.app using the `imsg` CLI.

### Prerequisites

- Install: `brew install steipete/tap/imsg`
- Grant Full Disk Access for terminal (System Settings → Privacy → Full Disk Access)
- Grant Automation permission for Messages.app when prompted

### Quick Reference

```bash
imsg chats --limit 10 --json
imsg history --chat-id 1 --limit 20 --json
imsg send --phone "+1234567890" --text "Hello from Hermes"
imsg send --chat "Chat Name" --text "Hello"
```

---

## macOS Computer Use

Drive the macOS desktop in the background using the `computer_use` tool. Actions do NOT move the user's cursor, steal keyboard focus, or switch Spaces.

### Canonical Workflow

1. **Capture first:**
```
computer_use(action="capture", mode="som", app="Safari")
```

2. **Click or type by SOM ID:**
```
computer_use(action="click", id=42)
computer_use(action="type", text="search query")
computer_use(action="key", name="Return")
```

3. **Scroll and drag:**
```
computer_use(action="scroll", direction="down", amount=300)
computer_use(action="drag", start_id=5, end_id=12)
```

### Rules
- Always capture before and after mutating actions.
- Click by SOM ID, never by raw coordinates.
- Use `find_and_click` for UI elements (buttons, fields, links).
- Verify the final state with a capture.
