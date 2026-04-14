# Static File Serving

> **Warning:** Do not use `default = true` in a custom resource when the app also has static file serving configured. The SPA fallback and the default resource conflict over routes. Use explicit named resources instead.

Serve frontend applications alongside your API.

## SPA Mode

For single-page applications (React, Vue, etc.), set `spa: true`. Unmatched paths serve `index.html` with status 200, letting the client-side router handle navigation. Route defaults to `/`.

```yaml
static:
  path: web
  spa: true
  build:
    sourceDir: source
    command: npm run build
```

The config key `static` is preferred. The aliases `static_files` and `staticFiles` are also accepted for backward compatibility.

To mount the SPA at a subpath instead of the root, add `route`:

```yaml
static:
  path: web
  spa: true
  route: /dashboard
```

Unmatched paths under `/dashboard/...` serve `index.html`. Paths outside `/dashboard` are unaffected.

## Plain Static Files

Without `spa`, Yeti serves files directly and returns 404 for unmatched paths. Use `route` to control the URL prefix.

```yaml
static:
  path: web
  route: /assets
```

## Directory Structure

```
~/yeti/applications/my-app/
  config.yaml
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

Build configuration lives inside the `static` block:

```yaml
static:
  path: web
  spa: true
  build:
    sourceDir: source          # Frontend project directory (default: "source")
    command: npm run build     # Build command (default: "npm run build")
```

`sourceDir` contains the frontend project (package.json, vite.config.ts, etc.). Build output must land in the directory specified by `path`.

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
