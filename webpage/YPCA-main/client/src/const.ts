export const COOKIE_NAME = "pca_auth_token";
export const ONE_YEAR_MS = 1000 * 60 * 60 * 24 * 365;

export const APP_TITLE = import.meta.env.VITE_APP_TITLE || "YPCA";

export const APP_LOGO =
  import.meta.env.VITE_APP_LOGO ||
  "https://placehold.co/128x128/E1E7EF/1F2937?text=YPCA";

export const USE_MOCK_AUTH =
  (import.meta.env.VITE_USE_MOCK_AUTH ?? "true").toLowerCase() !== "false";

const LOGIN_PATH = "/login";

const buildCurrentLocation = () => {
  if (typeof window === "undefined") return "/";
  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
};

const isSafeRedirect = (target: string | null | undefined) => {
  if (!target) return false;
  if (!target.startsWith("/")) return false;
  if (target.startsWith("//")) return false;
  return true;
};

export const getLoginUrl = (redirectOverride?: string) => {
  const redirectTarget = redirectOverride ?? buildCurrentLocation();
  const params = new URLSearchParams();

  if (isSafeRedirect(redirectTarget) && redirectTarget !== LOGIN_PATH) {
    params.set("redirect", redirectTarget);
  }

  const query = params.toString();
  return query ? `${LOGIN_PATH}?${query}` : LOGIN_PATH;
};
