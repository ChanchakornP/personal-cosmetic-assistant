# Personal Cosmetic Assistant (PCA) Frontend

Personal Cosmetic Assistant (PCA) is a React 19 single-page application that showcases a skincare assistant dashboard. The current repository contains only the frontend experience; it talks to an external API over tRPC when one is available, and provides graceful fallbacks when it is not.

## Feature Highlights

- **Home dashboard** summarising the product surface and quick actions.
- **Facial analysis, routine tracker, conflict analyser, recommendations, and profile** pages that demonstrate the target UX flow.
- **OAuth-style login flow** triggered from `/login`; the login button redirects to `VITE_OAUTH_PORTAL_URL` when configured, or stays on the local login page for demos.
- **Responsive layout** built with Tailwind CSS utilities, shadcn/ui components, and Wouter for routing.

## Requirements

- Node.js **18 LTS or newer** (Node 20 recommended). Older versions such as Node 10 cannot run Vite.
- npm 8+ (pnpm/yarn also work, but this guide uses npm).

## Getting Started

```bash
# Install dependencies
npm install

# Start the dev server on http://localhost:5173
npm run dev

# Create a production build in dist/public
npm run build

# Preview the production build locally
npm start
```

> **Note:** The dev server expects a backend tRPC endpoint at `/api/trpc`. If you do not have one running, pages that rely on API data will show empty states or surface console errors, but the UI will still render.

## Available npm Scripts

| Script            | Description                                                                 |
| ----------------- | --------------------------------------------------------------------------- |
| `npm run dev`     | Starts Vite in development mode.                                            |
| `npm run build`   | Bundles the client into `dist/public`.                                      |
| `npm start`       | Serves the built assets with `vite preview`.                                |
| `npm run check`   | Type-checks the project with the TypeScript compiler.                       |
| `npm run format`  | Formats files using Prettier. (Requires Node ≥14 to run the bundled binary.)|
| `npm run test`    | Runs the Vitest test suite (currently a placeholder).                       |
| `npm run db:push` | Leaves the original scaffolding command for Drizzle migrations—unused here. |

## Environment Variables

Create a `.env` file in the project root to customise runtime behaviour:

```
VITE_API_URL=http://localhost:3000         # tRPC HTTP endpoint (proxied by Vite dev server)
VITE_APP_TITLE=Personal Cosmetic Assistant  # App name displayed in the UI
VITE_APP_LOGO=https://example.com/logo.png  # Logo shown on the login page and header
VITE_OAUTH_PORTAL_URL=https://auth.example.com  # Optional OAuth portal. If omitted, /login stays local.
VITE_APP_ID=pca-frontend                    # Optional app identifier appended to the login redirect.
```

All values are optional; when they are absent, the UI falls back to sensible defaults defined in `client/src/const.ts`.

## Project Structure

```
client/
  public/               # Static assets served by Vite
  src/
    _core/hooks/        # Shared hooks (e.g. useAuth)
    components/         # UI components and layout primitives
    pages/              # Route-level components (Home, Login, etc.)
    lib/                # tRPC client and other shared utilities
    App.tsx             # Route configuration using Wouter
    main.tsx            # Application entry point
dist/                   # Build output (generated)
package.json            # npm scripts and dependencies
vite.config.ts          # Vite configuration
tsconfig.json           # TypeScript configuration
```

## Authentication Flow

- `client/src/const.ts#getLoginUrl` builds the OAuth redirect target. It warns and falls back to `/login` when `VITE_OAUTH_PORTAL_URL` is missing or invalid.
- `client/src/pages/Login.tsx` is a simple login hand-off page. Replace its contents with your own sign-in experience if you host authentication locally.
- `client/src/_core/hooks/useAuth.ts` encapsulates tRPC calls for `auth.me`/`auth.logout`. Without a backend, it defaults to an unauthenticated state.

## Styling and Components

- Tailwind CSS powers the design tokens defined in `client/src/index.css`.
- shadcn/ui provides accessible primitives inside `client/src/components/ui`.
- Custom layouts (for example `DashboardLayout`) keep the page shells consistent.

To adjust the look and feel, update the CSS variables or replace shadcn components with your preferred design system.

## Deployment Notes

1. Run `npm run build`.
2. Serve the contents of `dist/public/` behind your preferred static host (Vercel, Netlify, S3, nginx, etc.).
3. Ensure your API and OAuth endpoints are reachable from the deployed origin (`/api/trpc`, OAuth portal URL, cookies, CORS, etc.).

## Maintenance Tips

- Keep dependencies up to date with `npm outdated` and `npm update`.
- Upgrade Node.js periodically; Vite followsmodern Node releases quickly.
- Remove unused backend-specific scripts (e.g. `db:push`) if they are no longer relevant to your workflow.

---

Created by the PCA team as a frontend prototype. Feel free to fork and adapt it for your own cosmetic assistant experiments.
