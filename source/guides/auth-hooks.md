# Auth Hooks

Auth hooks let services override role resolution at request time, enabling tenant-based roles, subdomain permissions, or header-driven access control.

## The AuthHook Trait

```rust,ignore
#[async_trait]
pub trait AuthHook: Send + Sync {
    async fn on_resolve_role(
        &self,
        identity: &AuthIdentity,
        ctx: &Context,
    ) -> Option<Arc<dyn AccessControl>>;
}
```

If any hook returns `Some(access)`, default role resolution is skipped. If all return `None`, standard resolution proceeds (AppMembership lookup).

## AuthIdentity

An enum representing the authenticated user's identity:

| Variant | Fields | Description |
|---------|--------|-------------|
| `Basic` | `username` | HTTP Basic auth |
| `Jwt` | `username`, `claims` | JWT Bearer token |
| `OAuth` | `email`, `provider`, `claims` | OAuth session |
| `Mtls` | `username`, `cn`, `sans` | Client certificate |

Use `identity.username()` for a unified accessor (returns `Cow<str>`; OAuth falls back to `oauth:{provider}` when email is absent).

## AccessControl Trait

```rust,ignore
pub trait AccessControl: Send + Sync + std::fmt::Debug {
    fn is_super_user(&self) -> bool;
    fn role(&self) -> &str;
    fn username(&self) -> &str;
    fn can_read_table(&self, database: &str, table: &str) -> bool;
    fn can_insert_table(&self, database: &str, table: &str) -> bool;
    fn can_update_table(&self, database: &str, table: &str) -> bool;
    fn can_delete_table(&self, database: &str, table: &str) -> bool;
    fn can_read_attribute(&self, database: &str, table: &str, attr: &str) -> bool;
    fn can_write_attribute(&self, database: &str, table: &str, attr: &str) -> bool;
    fn has_unrestricted_attributes(&self, database: &str, table: &str) -> bool;
}
```

## Registering Hooks

```rust,ignore
impl Service for MyService {
    fn id(&self) -> &'static str { "my-auth-hook" }
    fn name(&self) -> &'static str { "My Auth Hook" }

    fn is_required(&self, _ctx: &StartupContext) -> bool { true }

    fn register(&self, ctx: &mut RegistrationContext) -> Result<()> {
        ctx.add_auth_hook(Arc::new(TenantHook::new()));
        Ok(())
    }
}
```

## Example: Tenant-Based Roles

```rust,ignore
pub struct TenantHook {
    tenant_roles: HashMap<String, Arc<dyn AccessControl>>,
}

#[async_trait]
impl AuthHook for TenantHook {
    async fn on_resolve_role(
        &self,
        identity: &AuthIdentity,
        ctx: &Context,
    ) -> Option<Arc<dyn AccessControl>> {
        let tenant_id = ctx.header("x-tenant-id")?;
        self.tenant_roles.get(tenant_id).cloned()
    }
}
```

## Execution Order

1. Request arrives with credentials
2. `AuthPipeline` produces an `AuthIdentity`
3. Each `AuthHook` is called in registration order
4. First `Some(access)` wins
5. All `None` falls through to default resolution (AppMembership lookup)

## Best Practices

- Return `None` to fall through when you have no opinion
- Keep hooks fast -- avoid database queries, or cache results
- Use hooks for cross-cutting concerns (tenancy, subdomain routing)
- `super_user` role cannot have privileges removed through hooks

## See Also

- [Roles & Permissions](auth-rbac.md) - Default RBAC system
- [Authentication Overview](auth-overview.md) - Auth providers
