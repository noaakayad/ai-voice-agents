# Design notes

A `Workflow` is independent of telephone infrastructure. Each call uses a `Session` holding the current stage and minimal structured state. A `Reply` describes the next utterance, termination or a department transfer. The optional classifier selects from a finite set of intents. The webhook translates replies to TwiML and validates incoming signatures. The local demo uses exactly the same workflow engine.

## Known limitations and roadmap

- Validate the optional Google Calendar adapter against a dedicated live test calendar, optimize availability queries and address cross-client booking races.
- Improve spoken date recognition without relying on unverified model-generated dates.
- Add robust silence handling, call event idempotency, concurrent call tests and persistent state with a retention policy.
- Add consent-aware voicemail and callback handling, secure access controls and a durable opt-out registry.
- Add a configurable fictional knowledge base for outreach questions and optional local feedback summarization.
- Add a live telephony integration test suite using controlled test numbers.

The original experimental approach used tool-calling agents and YAML prompts; this version deliberately uses explicit state transitions and an optional constrained LLM classifier instead. It does not preserve all previous implementation features.
