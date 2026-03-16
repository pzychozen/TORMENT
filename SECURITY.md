# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| < 2.1   | :x:                |

Only the latest release receives security updates.

## Reporting a Vulnerability

If you discover a security vulnerability in TORMENT, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please email: **[pzychozen@gmail.com]** with:

- A description of the vulnerability
- Steps to reproduce it
- The version of TORMENT you are running
- Any relevant logs or configuration (with sensitive data redacted)

## What to Expect

- You will receive an acknowledgment within **72 hours**
- A fix or mitigation plan within **14 days** for confirmed vulnerabilities
- Credit in the release notes (unless you prefer to remain anonymous)

## Scope

TORMENT runs a local HTTP service (`127.0.0.1:8787` by default). Security concerns include but are not limited to:

- Unauthorized access to memory data or workspace state
- Path traversal or injection through API endpoints
- Unintended data exposure through the REST API
- Issues with the embedding pipeline or external service calls

If you are running TORMENT on a public network (not recommended), additional precautions are your responsibility.
