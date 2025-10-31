import { getLoginUrl } from "@/const";
import { supabase } from "@/lib/supabase";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { User, Session, AuthError } from "@supabase/supabase-js";

type UseAuthOptions = {
  redirectOnUnauthenticated?: boolean;
  redirectPath?: string;
};

type UserProfile = {
  id: string;
  email?: string;
  emailVerified: boolean;
  name: string;
  avatar?: string;
  createdAt?: string;
};

export function useAuth(options?: UseAuthOptions) {
  const { redirectOnUnauthenticated = false, redirectPath = "/login" } =
    options ?? {};

  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  // Fetch user profile from profiles table
  const fetchUserProfile = useCallback(async (userId: string, currentUser?: User | null) => {
    try {
      const { data, error: profileError } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", userId)
        .single();

      if (profileError && profileError.code !== "PGRST116") {
        // PGRST116 is "not found" - ignore if profile doesn't exist yet
        console.warn("[useAuth] Profile fetch error:", profileError);
      }

      if (data && currentUser) {
        return {
          id: data.id,
          email: data.email || currentUser.email,
          emailVerified: currentUser.email_confirmed_at !== null,
          name: data.name || currentUser.user_metadata?.name || currentUser.email?.split("@")[0] || "User",
          avatar: data.avatar_url,
          createdAt: data.created_at || currentUser.created_at,
          ...data,
        };
      }
    } catch (err) {
      console.error("[useAuth] Error fetching profile:", err);
    }
    return null;
  }, []);

  // Initialize auth state
  useEffect(() => {
    let mounted = true;
    let timeoutId: NodeJS.Timeout;
    let sessionChecked = false;

    // Set a timeout to prevent infinite loading
    timeoutId = setTimeout(() => {
      if (mounted && !sessionChecked) {
        console.warn("[useAuth] Session check timeout, clearing invalid session");
        // Clear any invalid session
        supabase.auth.signOut().catch(() => { });
        setUser(null);
        setSession(null);
        setUserProfile(null);
        setError(null);
        setLoading(false);
      }
    }, 5000); // 5 second timeout

    // Get initial session with better error handling
    const checkSession = async () => {
      try {
        const { data: { session }, error }: {
          data: { session: Session | null };
          error: AuthError | null;
        } = await supabase.auth.getSession();

        if (!mounted) return;
        clearTimeout(timeoutId);
        sessionChecked = true;

        // Handle auth errors by clearing invalid session
        if (error) {
          console.warn("[useAuth] Session error:", error);
          // If it's an invalid token error, clear the session
          if (error.message?.includes("JWT") || error.message?.includes("token") || error.message?.includes("expired")) {
            await supabase.auth.signOut().catch(() => { });
          }
          setUser(null);
          setSession(null);
          setUserProfile(null);
          setError(error as Error);
          setLoading(false);
          return;
        }

        // Verify session is valid by checking expiration
        if (session) {
          const now = Math.floor(Date.now() / 1000);
          const expiresAt = session.expires_at;

          if (expiresAt && expiresAt < now) {
            console.warn("[useAuth] Session expired, clearing");
            await supabase.auth.signOut().catch(() => { });
            setSession(null);
            setUser(null);
            setUserProfile(null);
            setLoading(false);
            return;
          }
        }

        setSession(session);
        setUser(session?.user ?? null);

        if (session?.user) {
          fetchUserProfile(session.user.id, session.user).then((profile) => {
            if (!mounted) return;
            setUserProfile(profile);
          }).catch((err) => {
            console.warn("[useAuth] Profile fetch failed:", err);
          });
        } else {
          setUserProfile(null);
        }

        setLoading(false);
      } catch (err) {
        if (!mounted) return;
        clearTimeout(timeoutId);
        sessionChecked = true;
        console.error("[useAuth] Session check failed:", err);
        // Clear session on any unexpected error
        await supabase.auth.signOut().catch(() => { });
        setUser(null);
        setSession(null);
        setUserProfile(null);
        setError(err instanceof Error ? err : new Error(String(err)));
        setLoading(false);
      }
    };

    checkSession();

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event: string, session: Session | null) => {
      if (!mounted) return;

      // Handle specific auth events
      if (event === "SIGNED_OUT" || (event === "TOKEN_REFRESHED" && !session)) {
        setSession(null);
        setUser(null);
        setUserProfile(null);
        setError(null);
        setLoading(false);
        return;
      }

      // Check if session is expired
      if (session) {
        const now = Math.floor(Date.now() / 1000);
        const expiresAt = session.expires_at;

        if (expiresAt && expiresAt < now) {
          console.warn("[useAuth] Session expired in state change, clearing");
          await supabase.auth.signOut().catch(() => { });
          setSession(null);
          setUser(null);
          setUserProfile(null);
          setLoading(false);
          return;
        }
      }

      setSession(session);
      setUser(session?.user ?? null);
      setError(null);

      if (session?.user) {
        try {
          const profile = await fetchUserProfile(session.user.id, session.user);
          setUserProfile(profile);
        } catch (err) {
          console.warn("[useAuth] Profile fetch failed:", err);
        }
      } else {
        setUserProfile(null);
      }

      setLoading(false);
    });

    return () => {
      mounted = false;
      clearTimeout(timeoutId);
      subscription.unsubscribe();
    };
  }, [fetchUserProfile]);

  const signIn = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (authError) {
        throw authError;
      }

      if (data.user) {
        const profile = await fetchUserProfile(data.user.id, data.user);
        setUserProfile(profile);
      }

      return { user: data.user, session: data.session };
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [fetchUserProfile]);

  const signUp = useCallback(async (email: string, password: string, name?: string) => {
    setLoading(true);
    setError(null);
    try {
      const { data, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            name: name || email.split("@")[0],
          },
        },
      });

      if (authError) {
        throw authError;
      }

      if (data.user) {
        // Create profile entry
        const { error: profileError } = await supabase.from("profiles").insert({
          id: data.user.id,
          email,
          name: name || email.split("@")[0],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });

        if (profileError) {
          console.warn("[useAuth] Profile creation error:", profileError);
          // Don't throw - user is created, profile can be fixed later
        }

        const profile = await fetchUserProfile(data.user.id, data.user);
        setUserProfile(profile);
      }

      return { user: data.user, session: data.session };
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [fetchUserProfile]);

  const logout = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { error: authError } = await supabase.auth.signOut();
      if (authError) {
        throw authError;
      }
      setUser(null);
      setSession(null);
      setUserProfile(null);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    if (user?.id) {
      const profile = await fetchUserProfile(user.id, user);
      setUserProfile(profile);
    }
  }, [user, fetchUserProfile]);

  const state = useMemo(() => {
    const displayUser = userProfile || (user ? {
      id: user.id,
      email: user.email,
      emailVerified: user.email_confirmed_at !== null,
      name: user.user_metadata?.name || user.email?.split("@")[0] || "User",
      avatar: user.user_metadata?.avatar_url,
      createdAt: user.created_at,
    } : null);

    if (displayUser) {
      localStorage.setItem("pca-user-info", JSON.stringify(displayUser));
    } else {
      localStorage.removeItem("pca-user-info");
    }

    return {
      user: displayUser,
      loading,
      error,
      isAuthenticated: Boolean(user),
    };
  }, [user, userProfile, loading, error]);

  useEffect(() => {
    if (!redirectOnUnauthenticated) return;
    if (loading) return;
    if (user) return;
    if (typeof window === "undefined") return;
    if (window.location.pathname === redirectPath) return;

    window.location.href = redirectPath;
  }, [redirectOnUnauthenticated, redirectPath, loading, user]);

  return {
    ...state,
    session,
    refresh,
    logout,
    signIn,
    signUp,
  };
}
