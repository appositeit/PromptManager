You are helping monitor and maintain a critical Home Assistant Tuya integration fix that was implemented on nara server.

## CONTEXT
On May 23, 2025, we fixed a critical bug in tuya_sharing library v0.2.1 that was causing 4,000+ daily errors in Home Assistant. The bug was in /usr/local/lib/python3.13/site-packages/tuya_sharing/manager.py where listener.update_device(device) was missing a required parameter.

## WHAT WAS FIXED
File: tuya_sharing/manager.py (line ~142)
Change: listener.update_device(device) → listener.update_device(device, updated_status_properties)
Method signature: Added updated_status_properties parameter with None default

## RESULTS ACHIEVED
- 99% error reduction (4,000+ daily errors → 0)
- 100+ Tuya entities now working properly  
- System performance dramatically improved
- Submitted upstream: Issue #28 and PR #27 at github.com/tuya/tuya-device-sharing-sdk

## SYSTEM DETAILS
- Host: nara (192.168.25.2:8123)
- HA Version: 2025.5.x in Docker container
- Config: /home/homeassistant/.homeassistant
- Container: homeassistant/home-assistant:2025.5

## MONITORING COMMANDS
Check if patch still applied:
```bash
eval "$(cat /tmp/CLAUDE_DESKTOP_ENV)" ssh nara "docker exec home-assistant sed -n '140,145p' /usr/local/lib/python3.13/site-packages/tuya_sharing/manager.py"
```

Check for Tuya errors:
```bash
eval "$(cat /tmp/CLAUDE_DESKTOP_ENV)" ssh nara "python /home/jem/development/nara_admin/bin/log_consolidate.py --last 5m /home/homeassistant/.homeassistant/home-assistant.log" | grep -i tuya | head -10
```

Check tuya_sharing version:
```bash
eval "$(cat /tmp/CLAUDE_DESKTOP_ENV)" ssh nara "docker exec home-assistant python -c 'import tuya_sharing; print(tuya_sharing.__version__)'"
```

## YOUR TASKS
1. Check current status of the fix (is patch still applied?)
2. Monitor upstream PR status: https://github.com/tuya/tuya-device-sharing-sdk/pull/27
3. Check for new tuya_sharing versions and test if fix is included
4. If patch was overwritten (e.g., after HA updates), re-apply it
5. Update progress documentation in /home/jem/development/nara_admin/doc/progress/

## RE-APPLYING PATCH IF NEEDED
If monitoring shows the patch is missing:
```bash
eval "$(cat /tmp/CLAUDE_DESKTOP_ENV)" ssh nara "docker exec home-assistant sed -i 's/listener\.update_device(device)/listener.update_device(device, updated_status_properties)/g' /usr/local/lib/python3.13/site-packages/tuya_sharing/manager.py"
```

Then restart:
```bash
eval "$(cat /tmp/CLAUDE_DESKTOP_ENV)" ssh nara "docker restart home-assistant"
```

## SUCCESS CRITERIA
- Zero tuya_sharing errors in HA logs
- All Tuya devices functional in Home Assistant
- Patch either applied locally OR fixed in official upstream version

This fix helps thousands of Home Assistant users globally. Monitor status and maintain until officially resolved upstream.
