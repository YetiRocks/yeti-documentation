# OAuth Integration

Yeti supports OAuth 2.0 with GitHub, Google, and Microsoft providers.

## Setup

### 1. Register an OAuth Application

- **GitHub**: Settings > Developer settings > OAuth Apps
- **Google**: Cloud Console > APIs & Services > Credentials
- **Microsoft**: Azure Portal > App registrations

Callback URL: `https://your-host:port/yeti-auth/oauth_callback`

### 2. Configure Per-App OAuth in `Cargo.toml`

Provider credentials and role-mapping rules are declared in the app's `auth:` section. Values support `${ENV_VAR}` interpolation:

```yaml
auth:
  methods: [oauth]
  signup: auto
  default_role: viewer
  oauth:
    github:
      clientId: "${GITHUB_CLIENT_ID}"
      clientSecret: "${GITHUB_CLIENT_SECRET}"
    google:
      clientId: "${GOOGLE_CLIENT_ID}"
      clientSecret: "${GOOGLE_CLIENT_SECRET}"
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

Strategies: `provider` (match by provider name) or `email` (wildcard pattern). Rules evaluate in order; first match wins.

### Role Resolution on No Match

If no rule matches the user's provider or email, the user is **denied access** (401). No implicit default role exists for OAuth users. To allow all OAuth users, add a catch-all rule:

```yaml
rules:
  - strategy: provider
    pattern: "*"
    role: viewer
```

## Auto-Signup

When `signup: auto` is set (the default), users who authenticate via OAuth for the first time are automatically enrolled:

1. OAuth provider verifies identity and returns user info
2. Yeti checks for an existing AppMembership for `{appId}:{email}`
3. If no membership exists, one is created with the role determined by the matching rule
4. Subsequent requests use the stored membership

Set `signup: invite` to require pre-created memberships, or `signup: disabled` to block new users entirely.

## OAuth Flow

**1. Initiate**: Redirect to `GET /yeti-auth/oauth_login?provider=github`

**2. Callback**: Provider redirects to `/yeti-auth/oauth_callback` with authorization code. Yeti exchanges code for tokens, creates session, sets cookie.

**3. Use session**: Browser sends cookie automatically; or manually:

```bash
curl -sk --cookie "yeti_session=SESSION_ID" https://localhost:9996/my-app/MyTable
```

## Session Endpoints

```bash
# Current user info
curl -sk --cookie "yeti_session=SESSION_ID" https://localhost:9996/yeti-auth/oauth_user

# Logout (clears in-memory cache and database record)
curl -sk -X POST --cookie "yeti_session=SESSION_ID" https://localhost:9996/yeti-auth/oauth_logout

# Refresh provider token
curl -sk -X POST --cookie "yeti_session=SESSION_ID" https://localhost:9996/yeti-auth/oauth_refresh

# Available auth methods and roles for an app
curl -sk https://localhost:9996/yeti-auth/oauth_providers
```

## Session Storage

Two-tier: in-memory cache for fast lookup, OAuthSession table in the database for restart survival.

## Security

- CSRF token protection on login flow (10-minute expiry, in-memory DashMap with time-based + count-based sweep)
- Provider URLs validated at startup (SSRF protection -- rejects private IPs, requires HTTPS in production)
- Session cookies are httpOnly and secure (cookie name: `yeti_session`)
- Provider tokens stored server-side only

## Common Mistakes

- **Wrong callback URL**: The callback registered with your OAuth provider must exactly match `https://your-host:port/yeti-auth/oauth_callback`. A mismatch (trailing slash, wrong port, HTTP vs HTTPS) causes a silent redirect failure.
- **Missing HTTPS in production**: OAuth providers reject non-HTTPS callback URLs in production. Yeti also validates this at startup.
- **Credentials in config instead of env vars**: Use `${ENV_VAR}` syntax in the manifest. Values resolve from environment variables at startup.
- **No matching rule and no catch-all**: Without a matching rule, the user is denied after successful provider login. Add a fallback rule if you want all OAuth users to have access.

## See Also

- [Authentication Overview](auth-overview.md)
- [Roles & Permissions](auth-rbac.md) - How roles map to access
