# Postman collection

Generated from `docs/api/spec/*.json` (the official portal spec). Regenerate when the spec changes.

1. Postman → **Import** → drop both files:
   - `sha-eclaims.postman_collection.json` — all 49 endpoints, foldered by tag
   - `sha-uat.postman_environment.json` — base URL + credential variables
2. Select the **SHA UAT** environment (top-right) and fill `client_id` / `client_secret`
   from your `.env`. They are typed *secret* so they are masked and not exported. **Never commit them.**
3. Run **0 · Authentication → Get access token**. Its test script stores `access_token`.
   Every other request inherits it as a Bearer token, and the collection's pre-request script
   re-fetches it automatically when it expires (TTL 3600 s).
4. Try **Eligibility → GET /api/v1/patients/eligibility** with
   `identification_number=00000000`, `identification_type=National ID` — the UAT synthetic member.

Optional query params are present but disabled; enable as needed. `object[]` fields are `[]`
placeholders because the portal does not publish their inner schema (WORKFLOWS.md Q3).
