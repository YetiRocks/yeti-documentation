# OAuth Integration

Yeti supports OAuth 2.0 with GitHub, Google, and Microsoft providers.

## Setup

### 1. Register an OAuth Application

- **GitHub**: Settings > Developer settings > OAuth Apps
- **Google**: Cloud Console > APIs & Services > Credentials
- **Microsoft**: Azure Portal > App registrations

Callback URL: `https://your-host:9996/yeti-auth/oauth_callback`

### 2. Set Environment Variables

In your `.env` file:

```bash
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
```

### 3. Configure Per-App Rules

Map OAuth users to roles in your app's config:

```yaml
extensions:
  - yeti-auth:
      oauth:
        rules:
          - strategy: provider
            pattern: "google"
            role: admin
          - strategy: email
            pattern: "*@mycompany.com"
            role: standard
          - strategy: provider
            pattern: "github"
            role: standard
```

Strategies: `provider` (match by provider name) or `email` (wildcard pattern). Rules evaluate in order; first match wins. No match and no `default_role` returns `401`.

## OAuth Flow

**1. Initiate**: Redirect to `GET /yeti-auth/oauth_login?provider=github`

**2. Callback**: Provider redirects to `/yeti-auth/oauth_callback` with authorization code. Yeti exchanges code for tokens, creates session, sets cookie.

**3. Use session**: Browser sends cookie automatically; or manually:

```bash
curl -sk --cookie "session=SESSION_ID" https://localhost:9996/my-app/MyTable
```

## Session Endpoints

```bash
# Current user info
curl -sk --cookie "session=SESSION_ID" https://localhost:9996/yeti-auth/oauth_user

# Logout
curl -sk -X POST --cookie "session=SESSION_ID" https://localhost:9996/yeti-auth/oauth_logout

# Refresh provider token
curl -sk -X POST --cookie "session=SESSION_ID" https://localhost:9996/yeti-auth/oauth_refresh
```

## Session Storage

Two-tier: in-memory cache for fast lookup, database fallback for restart survival.

## Security

- CSRF token protection on login flow (10-minute expiry)
- Callback URLs validated at startup (SSRF protection, HTTPS required in production)
- Session cookies are httpOnly and secure
- Provider tokens stored server-side only

## See Also

- [Authentication Overview](auth-overview.md)
- [Roles & Permissions](auth-rbac.md) - How roles map to access
