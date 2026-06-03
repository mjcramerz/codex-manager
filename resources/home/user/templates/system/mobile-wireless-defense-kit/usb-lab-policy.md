# USB lab policy baseline

## Purpose
Reduce risk from USB emulation tools (BadUSB/Rubber Ducky class) during scoped lab exercises.

## Controls
- Allowlist documented USB VID/PID where feasible.
- Enforce endpoint alerts for rapid HID keystroke bursts.
- Block unknown USB mass-storage in sensitive zones.
- Require supervised physical access during exercise windows.

## Response
- Isolate endpoint on suspected USB-injection behavior.
- Preserve USB event and endpoint telemetry artifacts.
- Execute containment + credential hygiene playbook.
