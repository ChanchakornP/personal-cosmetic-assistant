import { USE_MOCK_AUTH, getLoginUrl } from "@/const";
import { trpc } from "@/lib/trpc";
import { TRPCClientError } from "@trpc/client";
import { useCallback, useEffect, useMemo, useState } from "react";

type StoredUser = Record<string, unknown> & {
  email?: string;
  name?: string;
};

const STORAGE_KEY = "pca-user-info";
const AUTH_EVENT = "pca-auth-change";

const readStoredUser = (): StoredUser | null => {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredUser;
  } catch (error) {
    console.warn("[auth] Failed to parse cached user payload", error);
    return null;
  }
};

const writeStoredUser = (user: StoredUser | null) => {
  if (typeof window === "undefined") return;
  if (!user) {
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
};

type UseAuthOptions = {
  redirectOnUnauthenticated?: boolean;
  redirectPath?: string;
};

export function useAuth(options?: UseAuthOptions) {
  const redirectOnUnauthenticated = options?.redirectOnUnauthenticated ?? false;
  const redirectPath = options?.redirectPath ?? getLoginUrl();

  if (USE_MOCK_AUTH) {
    const [user, setUser] = useState<StoredUser | null>(() => readStoredUser());

    useEffect(() => {
      writeStoredUser(user);
    }, [user]);

    useEffect(() => {
      if (typeof window === "undefined") return;
      const handleStorage = (event: StorageEvent) => {
        if (event.key !== STORAGE_KEY) return;
        setUser(readStoredUser());
      };
      const handleCustom = () => setUser(readStoredUser());

      window.addEventListener("storage", handleStorage);
      window.addEventListener(AUTH_EVENT, handleCustom);

      return () => {
        window.removeEventListener("storage", handleStorage);
        window.removeEventListener(AUTH_EVENT, handleCustom);
      };
    }, []);

    const logout = useCallback(async () => {
      setUser(null);
      writeStoredUser(null);
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent(AUTH_EVENT));
      }
    }, []);

    const state = useMemo(
      () => ({
        user,
        loading: false,
        error: null,
        isAuthenticated: Boolean(user),
      }),
      [user]
    );

    useEffect(() => {
      if (!redirectOnUnauthenticated) return;
      if (state.user) return;
      if (typeof window === "undefined") return;
      if (window.location.pathname === "/login") return;

      window.location.href = redirectPath;
    }, [redirectOnUnauthenticated, redirectPath, state.user]);

    return {
      ...state,
      refresh: async () => state,
      logout,
    };
  }

  const utils = trpc.useUtils();

  const meQuery = trpc.auth.me.useQuery(undefined, {
    retry: false,
    refetchOnWindowFocus: false,
  });

  const logoutMutation = trpc.auth.logout.useMutation({
    onSuccess: () => {
      utils.auth.me.setData(undefined, null);
    },
  });

  const logout = useCallback(async () => {
    try {
      await logoutMutation.mutateAsync();
    } catch (error: unknown) {
      if (
        error instanceof TRPCClientError &&
        error.data?.code === "UNAUTHORIZED"
      ) {
        return;
      }
      throw error;
    } finally {
      utils.auth.me.setData(undefined, null);
      await utils.auth.me.invalidate();
    }
  }, [logoutMutation, utils]);

  const state = useMemo(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(meQuery.data ?? null)
      );
    }
    return {
      user: meQuery.data ?? null,
      loading: meQuery.isLoading || logoutMutation.isPending,
      error: meQuery.error ?? logoutMutation.error ?? null,
      isAuthenticated: Boolean(meQuery.data),
    };
  }, [
    meQuery.data,
    meQuery.error,
    meQuery.isLoading,
    logoutMutation.error,
    logoutMutation.isPending,
  ]);

  useEffect(() => {
    if (!redirectOnUnauthenticated) return;
    if (meQuery.isLoading || logoutMutation.isPending) return;
    if (state.user) return;
    if (typeof window === "undefined") return;
    if (window.location.pathname === "/login") return;

    window.location.href = redirectPath;
  }, [
    redirectOnUnauthenticated,
    redirectPath,
    logoutMutation.isPending,
    meQuery.isLoading,
    state.user,
  ]);

  return {
    ...state,
    refresh: () => meQuery.refetch(),
    logout,
  };
}
