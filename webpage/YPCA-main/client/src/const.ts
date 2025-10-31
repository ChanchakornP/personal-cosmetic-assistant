export const COOKIE_NAME = "pca_auth_token";
export const ONE_YEAR_MS = 1000 * 60 * 60 * 24 * 365;

export const APP_TITLE = import.meta.env.VITE_APP_TITLE || "YPCA";

export const APP_LOGO =
  import.meta.env.VITE_APP_LOGO ||
  "https://placehold.co/128x128/E1E7EF/1F2937?text=YPCA";

// Generate login URL at runtime so redirect URI reflects the current origin.
export const getLoginUrl = () => {
  const oauthPortalUrl = import.meta.env.VITE_OAUTH_PORTAL_URL;
  if (!oauthPortalUrl) {
    console.warn(
      "[auth] Missing VITE_OAUTH_PORTAL_URL; using local /login fallback."
    );
    return "/login";
  }

  const appId = import.meta.env.VITE_APP_ID ?? "local-app";
  const redirectUri = `${window.location.origin}/api/oauth/callback`;
  const state = btoa(redirectUri);

  let url: URL;
  try {
    url = new URL("app-auth", oauthPortalUrl.endsWith("/")
      ? oauthPortalUrl
      : `${oauthPortalUrl}/`);
  } catch (error) {
    console.error("[auth] Invalid VITE_OAUTH_PORTAL_URL", error);
    return "/login";
  }
  url.searchParams.set("appId", appId);
  url.searchParams.set("redirectUri", redirectUri);
  url.searchParams.set("state", state);
  url.searchParams.set("type", "signIn");

  return url.toString();
};
