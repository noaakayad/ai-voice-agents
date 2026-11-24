# Security and privacy

Never commit credentials, OAuth tokens, phone numbers, customer information, private scripts or recordings. Rotate any credentials that were ever embedded in earlier code. Use dedicated test accounts and least-privilege credentials.

The telephone adapter validates Twilio request signatures, restricts transfers to configured destinations, and uses bounded in-memory session state. Do not expose the development server as a production service. Add rate limits, replay/idempotency protection, appropriate authentication, monitoring and durable privacy-aware state before deployment.

Obtain consent for automated calls and any third-party processing. Do not use the sample for unsolicited or bulk calls. The sample does not implement a durable do-not-call list; real deployment must enforce one externally. Avoid entering real customer information. Report vulnerabilities privately to the repository maintainer once a contact channel is established.
