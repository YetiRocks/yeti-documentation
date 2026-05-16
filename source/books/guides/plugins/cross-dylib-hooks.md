# Cross-Dylib Hooks

Plugin-apps (dylib-compiled apps with `plugin = true` in `[package.metadata.app]`) can install `tower::Service<R>` instances into a static plugin's hook registry across the cdylib boundary. This is how a customer-authored `plugin-auth-okta` extends yeti-auth's OAuth pipeline without recompiling the host binary, and how `plugin-mcp-yeti` adds tools to yeti-mcp's MCP endpoint.

The mechanism is the YTC-367 hook-registration bridge (see [ADR-009](https://github.com/yetirocks/yeti-core/blob/main/docs/adr/009-cross-dylib-hook-registration.md) for the full design). This page covers the user-facing API.

## The `Plugin::register_hooks` Lifecycle Method

Added to the `Plugin` trait in yeti-types:

```rust,ignore
pub trait Plugin: Send + Sync + 'static {
    // ... existing methods ...

    /// Register cross-dylib hook services. Called by the app loader
    /// between `resources()` and `on_ready()`. Default-empty so
    /// existing plugins compile unchanged.
    fn register_hooks(&self) -> Result<()> { Ok(()) }
}
```

Inside `register_hooks`, plugin authors build typed `Service<Req, Resp, E>` instances and call `yeti_sdk::service_bridge::register_hook` with the versioned chain name for each one. The SDK helper wraps the typed service in a `BytesAdapter`, boxes it as `BoxCloneSyncService<Bytes, Bytes, BridgeError>`, and FFI-calls into the host's `HookRegistry`. Plugin authors never touch bytes or unsafe code.

## Registering a Hook

```rust,ignore
use yeti_sdk::plugins::Plugin;
use yeti_sdk::prelude::extension::oauth::{
    OAUTH_HOOK_CHAIN_NAME, OAuthRequest, OAuthResponse, OAuthService,
};
use yeti_sdk::prelude::{BoxCloneSyncService, service_fn};
use yeti_sdk::error::{Result, YetiError};

impl Plugin for MyOktaPlugin {
    fn id(&self) -> &'static str { "plugin-auth-okta" }
    fn is_plugin(&self) -> bool { true }

    fn register_hooks(&self) -> Result<()> {
        let svc: OAuthService = BoxCloneSyncService::new(
            service_fn(|mut req: OAuthRequest| async move {
                // Mutate req.user based on req.profile claims
                // ...
                Ok::<_, YetiError>(OAuthResponse(req.user))
            })
        );

        yeti_sdk::service_bridge::register_hook::<
            OAuthService, OAuthRequest, OAuthResponse, YetiError,
        >(OAUTH_HOOK_CHAIN_NAME, svc)
            .map_err(|e| YetiError::Internal(format!("oauth hook reg: {e}")))?;

        Ok(())
    }
}
```

## Available Hook Chains

Hook chain names are versioned `&'static str` constants that live in `yeti_sdk::prelude::extension::{module}::*`. When the wire shape of a chain's `Request`/`Response` changes incompatibly, the static plugin ships a `v2` alongside, reads both chains, and lets v1 plugins age out.

| Chain name | Static plugin | Request → Response | Semantics |
|---|---|---|---|
| `yeti.auth.oauth.v1` | yeti-auth | `OAuthRequest` → `OAuthResponse` | Pipeline. Each registered service mutates the User row; runs in registration order. |
| `yeti.auth.token.v1` | yeti-auth | `TokenRequest` → `TokenResponse` | Pipeline. Each service extends the JWT `extra` claims map. |
| `yeti.mcp.list_tools.v1` | yeti-mcp | `ListToolsRequest` → `ListToolsResponse` | Accumulator. Each service receives the in-progress tool list, appends or replaces, returns the next-stage list. |
| `yeti.mcp.call_tool.v1` | yeti-mcp | `CallToolRequest` → `CallToolResponse` | Dispatcher. First service to return `Some(value)` wins; `None` falls through to the next service / auto-inventory CRUD dispatch. |

Each `Request`/`Response` type is `Serialize + DeserializeOwned`; the bridge bincode-encodes the typed payload across the FFI boundary. `serde_json::Value` fields ride the wire as JSON-encoded strings (bincode 1.3 cannot round-trip `Value` directly).

## Multi-Service Registration

`Plugin::register_hooks` is called once per plugin load. Calling `register_hook` multiple times for the same chain name appends to the chain — useful when one plugin installs services for multiple hooks. For example, `plugin-auth-okta` registers both an OAuth service and a Token service:

```rust,ignore
fn register_hooks(&self) -> Result<()> {
    yeti_sdk::service_bridge::register_hook::<OAuthService, _, _, _>(
        OAUTH_HOOK_CHAIN_NAME, build_oauth_service(self.config()),
    )?;
    yeti_sdk::service_bridge::register_hook::<TokenService, _, _, _>(
        TOKEN_HOOK_CHAIN_NAME, build_token_service(self.config()),
    )?;
    Ok(())
}
```

## Dispatch Semantics

Static plugins call `yeti_sdk::service_bridge::dispatch_hook_chain::<Req, Resp>(name, req)` from inside their own per-request lifecycle methods to thread requests through every registered service. The same call works from dylib code (going across the FFI boundary) and from host code (same process, same FFI symbols).

`BridgeError::NotFound` from the dispatcher means no plugin has registered into that chain — the static plugin treats this as "no bridged hooks, in-process Vec only" rather than propagating the error.

## Worked Examples

Two reference plugin-apps in production demonstrate the pattern end-to-end:

- **[`plugin-auth-okta`](https://github.com/YetiRocks/plugin-auth-okta)** — Okta-style claim mapping for yeti-auth. Maps a configured OAuth claim path (e.g. `groups[0]`) to a Yeti role and embeds raw provider claims in JWTs under `extra.okta.{key}`. Use this as a starting point for any IDP integration (Azure AD, Auth0, OneLogin, Ping).
- **[`plugin-mcp-yeti`](https://github.com/YetiRocks/plugin-mcp-yeti)** — extends yeti-mcp's tool registry. Stub that adds one `yeti_hello` tool to demonstrate the McpHooks bridge. Use as a starting point for custom-domain tool servers, organization knowledge bases, or third-party service connectors.

Both repos ship as `plugin = true` apps; clone into your `{rootDirectory}/applications/`, edit, restart yeti.

## Verifying Hook Registration

After `yeti start`, look in `{rootDirectory}/logs/yeti.log` for the plugin's own `register_hooks` log line. The reference plugins both emit a signal of the form:

```
INFO plugin: [plugin-{name}] register_hooks called; building services
INFO plugin: [plugin-{name}] Registered {hook description} via {chain1} / {chain2}
INFO yeti_server::app_loader: ✓ Started plugin-{name} elapsed={time}s
```

If `register_hooks` doesn't run, the most common cause is missing `plugin = true` in `Cargo.toml` `[package.metadata.app]`, or missing `resources = { path = "resources/*.rs" }` (without it the compiler scaffolder won't pick up the `impl Plugin for ...` declaration). Confirm with the host log lines `Discovered filesystem plugin: {name}` → `Starting application: {name}` → `register_hooks called`.

## Design References

- [ADR-009: Cross-Dylib Hook Registration](https://github.com/yetirocks/yeti-core/blob/main/docs/adr/009-cross-dylib-hook-registration.md) — full design rationale, wire shape, LTO retention gotcha
- [ADR-008: Plugin Author Contract](https://github.com/yetirocks/yeti-core/blob/main/docs/adr/008-plugin-author-contract.md) — the broader plugin-app naming + registration conventions
- [YTC-367](https://linear.app/yetirocks/issue/YTC-367) — bridge implementation tracking
