# Auth Hooks

Auth hooks let extensions override role resolution at request time, enabling tenant-based roles, subdomain permissions, or header-driven access control.

## The AuthHook Trait

```rust
#[async_trait::async_trait]
pub trait AuthHook: Send + Sync {
    async fn on_resolve_role(
        &self,
        identity: &AuthIdentity,
        params: &ResourceParams,
    ) -> Option<Arc<dyn AccessControl>>;
}
```

If any hook returns `Some(access)`, default role resolution is skipped. If all return `None`, standard resolution proceeds.

## AuthIdentity

| Field | Type | Description |
|-------|------|-------------|
| `username` | `String` | Authenticated username |
| `provider` | `String` | Auth provider ("basic", "jwt", "oauth") |
| `claims` | `Option<Value>` | JWT claims or OAuth user data |
| `role_id` | `Option<String>` | Role ID from User record |

## AccessControl Trait

```rust
pub trait AccessControl: Send + Sync + std::fmt::Debug {
    fn is_super_user(&self) -> bool;
    fn username(&self) -> &str;
    fn can_read_table(&self, database: &str, table: &str) -> bool;
    fn can_insert_table(&self, database: &str, table: &str) -> bool;
    fn can_update_table(&self, database: &str, table: &str) -> bool;
    fn can_delete_table(&self, database: &str, table: &str) -> bool;
    fn can_read_attribute(&self, database: &str, table: &str, attr: &str) -> bool;
    fn can_write_attribute(&self, database: &str, table: &str, attr: &str) -> bool;
}
```

## Registering Hooks

```rust
impl Extension for MyExtension {
    fn name(&self) -> &str { "my-auth-hook" }

    fn auth_hooks(&self) -> Vec<Arc<dyn AuthHook>> {
        vec![Arc::new(TenantHook::new())]
    }
}
```

## Example: Tenant-Based Roles

```rust
pub struct TenantHook {
    tenant_roles: HashMap<String, Arc<dyn AccessControl>>,
}

#[async_trait::async_trait]
impl AuthHook for TenantHook {
    async fn on_resolve_role(
        &self,
        identity: &AuthIdentity,
        params: &ResourceParams,
    ) -> Option<Arc<dyn AccessControl>> {
        let tenant_id = params.header("x-tenant-id")?;
        self.tenant_roles.get(tenant_id).cloned()
    }
}
```

## Execution Order

1. Request arrives with credentials
2. `AuthPipeline` produces `AuthIdentity`
3. Each `AuthHook` called in order
4. First `Some(access)` wins
5. All `None` falls through to default role resolution

## Best Practices

- Return `None` to fall through when you have no opinion
- Keep hooks fast - avoid database queries, or cache results
- Use hooks for cross-cutting concerns (tenancy, subdomain routing)
- `super_user` role cannot have privileges removed through hooks

## See Also

- [Roles & Permissions](auth-rbac.md) - Default RBAC system
- [Building Extensions](building-extensions.md) - Extension development
- [Basic Authentication](auth-basic.md) - Basic auth details
