# Static File Serving

Yeti serves frontend applications alongside your API.

## Configuration

```yaml
static_files:
  path: web          # Directory relative to app dir
  route: "/"         # URL prefix
  index: index.html  # Default file for directory requests
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
```

Served at:
- `https://localhost:9996/my-app/` -> `web/index.html`
- `https://localhost:9996/my-app/assets/main.js` -> `web/assets/main.js`

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

```yaml
static_files:
  path: web/dist
  route: "/"
  index: index.html
```

## SPA Routing

The `index` config ensures unmatched routes fall back to `index.html`, so client-side routing (React Router, Vue Router) works with deep links. Custom resources take priority over static files for matched routes.

## Content Types

Automatic based on extension: `.html` -> `text/html`, `.css` -> `text/css`, `.js` -> `application/javascript`, `.json` -> `application/json`, `.png` -> `image/png`, `.svg` -> `image/svg+xml`, `.woff2` -> `font/woff2`.

## API Coexistence

Table endpoints and custom resources are matched first; static files serve as fallback for unmatched paths.
