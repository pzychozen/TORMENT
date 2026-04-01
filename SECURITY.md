# Security Policy

## Supported Versions

Only the current supported release line receives security updates.

| Version | Supported |
| ------- | --------- |
| 2.1.x   | ✅         |
| < 2.1   | ❌         |

Older versions may contain known issues and may not receive fixes.

## Reporting a Vulnerability

If you believe you have found a security vulnerability in TORMENT, please report it responsibly.

Please **do not open a public GitHub issue** for suspected security vulnerabilities.

Instead, email: **[pzychozen@gmail.com](mailto:pzychozen@gmail.com)**

Please include as much of the following as possible:

* a clear description of the issue
* steps to reproduce it
* affected version / commit / branch
* whether the issue is local-only or exposed over a network
* proof-of-concept, request sample, or test case if available
* relevant logs or configuration details, with secrets redacted

## What to Expect

* acknowledgment within **72 hours** when possible
* triage and validation for credible reports
* a fix, mitigation, or decision note for confirmed issues
* credit in release notes if a fix is shipped, unless you prefer to remain anonymous

Response times may vary depending on severity, complexity, and maintainer availability.

## Scope

TORMENT primarily runs as a local HTTP service on **127.0.0.1:8787** by default.

Security concerns may include:

* unauthorized access to memory data, workspace state, or agent state
* path traversal, path injection, or unsafe filesystem access
* unintended data exposure through API endpoints
* unsafe handling of archive, deep memory, checkpoint, or embedding storage
* vulnerabilities involving promotion, compression, or collective-memory flows
* issues involving authentication, authorization, or trust boundaries
* issues involving embedding providers or external service calls

## Out of Scope

The following are generally out of scope unless they directly cause a security impact in TORMENT itself:

* feature requests
* performance-only issues
* crashes without security impact
* issues only affecting unsupported versions
* insecure deployments that intentionally expose TORMENT to public networks without additional hardening
* vulnerabilities in third-party software or local system configuration unless TORMENT introduces or worsens the risk

## Deployment Notice

TORMENT is designed primarily for local or otherwise controlled environments.

If you choose to expose TORMENT on a public or untrusted network, you are responsible for additional safeguards such as:

* reverse proxy hardening
* authentication and access control
* firewall / network restrictions
* TLS / transport protection
* host-level isolation and monitoring

## Disclosure

Please allow reasonable time for validation and mitigation before public disclosure.

Reports that are incomplete, non-reproducible, abusive, or clearly automated spam may be closed without action.
