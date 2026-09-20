# Authentication

> Source: https://afyaconnect.dha.go.ke/hie-api/auth/authentication · API: **Authentication and Authorization** v1.0.0 · captured 2026-09-20

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware/api/v1`

Operations related to user authentication and token management.

## Endpoints

- [`POST /tenants/token`](#post-tenantstoken-get-access-token) — Get access token

---

### `POST /tenants/token` — Get access token

- **Auth:** none (public)
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/tenants/token`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/auth/authentication#get-access-token

Obtains an access token used for subsequent API calls

**Related documentation:** [OAuth Flow](/docs/authentication/process/oauth-flow), [Authentication Best Practices](/docs/authentication/guides/best-practices)

**Request body** — `application/x-www-form-urlencoded`, required

OAuth2 client credentials

| Field | Type | Required | Description |
|---|---|---|---|
| `client_id` | string | **yes** | OAuth2 client ID. Example value is dummy data. |
| `client_secret` | string | **yes** | OAuth2 client secret. Example value is dummy data. |

<details><summary>Example request body</summary>

```json
{
  "client_id": "client_id",
  "client_secret": "client_secret"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/tenants/token' \
  --header 'Content-Type: application/json' \
  --data '{
  "client_id": "client_id",
  "client_secret": "client_secret"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — OK</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `access_token` | string | no |  |
| `expires_in` | integer | no |  |
| `token_type` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "access_token": "access_token",
  "expires_in": 0,
  "token_type": "token_type"
}
```

</details>

<details><summary><code>400</code> — Bad Request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>


---
