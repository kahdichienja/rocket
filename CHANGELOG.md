# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com), versioning: [SemVer](https://semver.org).

## [Unreleased]
### Added
- Project skeleton, quality gates (ruff, mypy strict, import-linter, pytest ≥ 90 % coverage), CI.
- Endpoint reference and workflow documentation generated from the DHA AfyaConnect portal.
- `AsyncSHAClient` with OAuth2 client-credentials auth (cached, single-flight refresh, 401 replay), idempotent-only retries with jittered backoff, typed error translation (incl. `trace_id`).
- `sha.eligibility.check()` — `GET /patients/eligibility` mapped to an `Eligibility` read model; verified against DHA UAT.
- Domain value objects: identifiers (redacted `ConsentToken`), ICD/intervention codes, `Money`, documented enums, lenient server-status enums.
