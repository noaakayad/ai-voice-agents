# Appointment scheduling

The offline calendar stores only local in-memory intervals and prevents overlapping reservations. Working hours are 09:00–17:00 on weekdays. An optional Google Calendar adapter is available for the telephone demo; see the main README for setup. It has not been tested against a live calendar.

## Run locally

```sh
python -m voice_agents.demo appointments
```

## Example dialogue

```text
You: YYYY-MM-DD HH:MM (choose a future weekday)
Agent: The available appointment is ... Confirm?
You: yes
Agent: Your appointment is confirmed ...
```

[Back to project overview](../../README.md)
