# AfyaConnect HIE — API Reference (eClaims + Auth)

Generated 2026-09-20 from the developer portal's server-side props (`/_next/data/<build>/hie-api/...json`), which is the same OpenAPI-derived AST the portal renders. Raw captures are in [spec/](spec/) for contract tests.

Each endpoint includes the portal's example request/response JSON (`spec/examples.json`), which exposes the nested object shapes the field tables flatten.

**Caveat:** the portal flattens `oneOf`/`anyOf` request schemas. Where a description says "choose one strategy" (e.g. OTP vs biometrics) but every field shows as required, trust the description; verify against the UAT sandbox before hard-coding validation.

| API | Tag | Endpoints | File |
|---|---|---|---|
| Authentication and Authorization | Authentication | 1 | [auth--authentication.md](auth--authentication.md) |
| eClaims and Preauth APIs | Eligibility | 6 | [eclaims--eligibility.md](eclaims--eligibility.md) |
| eClaims and Preauth APIs | Authorizations | 3 | [eclaims--authorizations.md](eclaims--authorizations.md) |
| eClaims and Preauth APIs | Start Visit Consent | 1 | [eclaims--start-visit-consent.md](eclaims--start-visit-consent.md) |
| eClaims and Preauth APIs | Interventions | 4 | [eclaims--interventions.md](eclaims--interventions.md) |
| eClaims and Preauth APIs | Preauths | 5 | [eclaims--preauths.md](eclaims--preauths.md) |
| eClaims and Preauth APIs | Billing | 13 | [eclaims--billing.md](eclaims--billing.md) |
| eClaims and Preauth APIs | Preauth Doctor Consent | 1 | [eclaims--preauth-doctor-consent.md](eclaims--preauth-doctor-consent.md) |
| eClaims and Preauth APIs | ePrescriptions | 4 | [eclaims--eprescriptions.md](eclaims--eprescriptions.md) |
| eClaims and Preauth APIs | Claim Dispatch | 5 | [eclaims--claim-dispatch.md](eclaims--claim-dispatch.md) |
| eClaims and Preauth APIs | Emergency | 6 | [eclaims--emergency.md](eclaims--emergency.md) |

## Servers

| API | UAT base URL |
|---|---|
| Authentication and Authorization | `https://ilm-dev.dha.go.ke/uat-middleware/api/v1` |
| eClaims and Preauth APIs | `https://ilm-dev.dha.go.ke/uat-middleware` (paths already include `/api/v1`) |

Production base URL is **not** published on the portal; obtain it from DHA onboarding.

