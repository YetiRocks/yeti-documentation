# Static File Serving

> **Warning:** Do not use `default = true` in a custom resource when the app also has static file serving configured. The SPA fallback and the default resource conflict over routes. Use explicit named resources instead.

Serve frontend applications alongside your API.

## SPA Mode

For single-page applications (React, Vue, etc.), set `spa: true`. Unmatched paths serve `index.html` with status 200, letting the client-side router handle navigation. Route defaults to `/`.

```toml
[package.metadata.app]
static = { path = "web", spa = true, source = "source", build = "npm run build" }
```

To mount the SPA at a subpath instead of the root, set `root`:

```toml
[package.metadata.app]
static = { path = "web", root = "/dashboard", spa = true }
```

Unmatched paths under `/dashboard/...` serve `index.html`. Paths outside `/dashboard` are unaffected.

## Plain Static Files

Without `spa`, Yeti serves files directly and returns 404 for unmatched
paths (or your custom `not_found` page). Use `root` to control the URL
prefix.

```toml
[package.metadata.app]
static = { path = "web", root = "/assets" }
```

## Custom 404

Author a `404.html` and wire it via `not_found`:

```toml
[package.metadata.app]
static = { path = "web", not_found = "404.html" }
```

The server returns 404 status with the file as the body. With `spa = true`
**and** `not_found` set, the explicit 404 wins for missing files; the SPA
fallback only fires for paths that haven't been served as files.

## Directory Structure

```
~/yeti/applications/my-app/
  Cargo.toml
  web/
    index.html
    assets/
      main.js
      style.css
    pages/
      about.html
```

Served at:
- `https://localhost:9996/my-app/` -> `web/index.html`
- `https://localhost:9996/my-app/assets/main.js` -> `web/assets/main.js`
- `https://localhost:9996/my-app/pages/about.html` -> `web/pages/about.html`

Subfolders work in both SPA and plain modes. The only difference is what happens when a path doesn't match any file.

## Build Pipelines

Set `source` (the frontend project dir, default `"source"`) and `build`
(the build command). Build output must land in the directory named by
`path`.

```toml
[package.metadata.app]
static = { path = "web", spa = true, source = "source", build = "npm run build" }
```

## Vite Integration

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/my-app/',  // Must match app_id
  build: { outDir: 'dist' },
})
```

## Content Types

Automatic based on extension: `.html` -> `text/html`, `.css` -> `text/css`, `.js` -> `application/javascript`, `.json` -> `application/json`, `.png` -> `image/png`, `.svg` -> `image/svg+xml`, `.woff2` -> `font/woff2`.

## API Coexistence

Table endpoints and custom resources are matched first; static files serve as fallback for unmatched paths.

## Advanced Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | string | - | Directory containing static files (relative to app directory) |
| `route` | string | `"/"` | URL route prefix |
| `spa` | boolean | `false` | Enable SPA mode (serve index.html for unmatched paths) |
| `index` | string | `"index.html"` | Default file for directory requests |
| `notFound` | object | - | Custom 404 page (overrides SPA default). Use `{ file: "404.html", statusCode: 404 }` |
| `build` | object | - | Frontend build configuration |
| `build.sourceDir` | string | `"source"` | Frontend project directory |
| `build.command` | string | `"npm run build"` | Build command to run |
