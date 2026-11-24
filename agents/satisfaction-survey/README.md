# Satisfaction survey

The prototype stores only structured state temporarily. It records whether feedback was supplied, not its text. No survey data is exported.

## Run locally

```sh
python -m voice_agents.demo survey
```

## Example dialogue

```text
You: yes
Agent: How would you rate your support experience from zero to five?
You: 4
Agent: Was your issue resolved? Yes or no.
You: yes
Agent: Any optional feedback? Say skip to omit it.
You: skip
Agent: Thank you for your feedback. Goodbye.
```

[Back to project overview](../../README.md)
