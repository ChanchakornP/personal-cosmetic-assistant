export const COOKIE_NAME = "pca_auth_token";
export const ONE_YEAR_MS = 1000 * 60 * 60 * 24 * 365;

export const APP_TITLE = import.meta.env.VITE_APP_TITLE || "YPCA";

export const APP_LOGO = "/logo.svg";

// Supabase configuration
export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Simple login URL (now just a route path)
export const getLoginUrl = () => {
  return "/login";
};
