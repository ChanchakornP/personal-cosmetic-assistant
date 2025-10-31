import { APP_LOGO, APP_TITLE, USE_MOCK_AUTH } from "@/const";
import { Loader2 } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { useLocation } from "wouter";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { trpc } from "@/lib/trpc";
import { TRPCClientError } from "@trpc/client";

const resolveRedirect = () => {
  if (typeof window === "undefined") return "/";
  const search = window.location.search;
  const params = new URLSearchParams(search);
  const raw = params.get("redirect");
  if (!raw) return "/";
  if (!raw.startsWith("/") || raw.startsWith("//")) return "/";
  return raw || "/";
};

const STORAGE_KEY = "pca-user-info";
const AUTH_EVENT = "pca-auth-change";

function Login() {
  const [location] = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [mockSubmitting, setMockSubmitting] = useState(false);

  const redirectTarget = useMemo(() => resolveRedirect(), [location]);

  const utils = trpc.useUtils();
  const loginMutation = trpc.auth.login.useMutation();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);

    if (!email || !password) {
      setFormError("Please enter both email and password.");
      return;
    }

    try {
      if (USE_MOCK_AUTH) {
        setMockSubmitting(true);
        const mockUser = {
          email,
          name: email.split("@")[0] ?? "User",
        };
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
        window.dispatchEvent(
          new CustomEvent(AUTH_EVENT, { detail: mockUser })
        );
        window.location.href = redirectTarget;
        return;
      }

      await loginMutation.mutateAsync({ email, password });
      await utils.auth.me.invalidate();
      window.location.href = redirectTarget;
    } catch (error) {
      if (error instanceof TRPCClientError) {
        setFormError(error.message || "Login failed. Please try again later.");
        return;
      }
      setFormError("Login failed. Please try again later.");
    } finally {
      if (USE_MOCK_AUTH) {
        setMockSubmitting(false);
      }
    }
  };

  const isSubmitting = USE_MOCK_AUTH
    ? mockSubmitting
    : loginMutation.isPending;

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50 flex items-center justify-center px-4 py-16">
      <Card className="w-full max-w-md border-0 shadow-lg">
        <CardHeader className="items-center text-center">
          <img
            src={APP_LOGO}
            alt={`${APP_TITLE} logo`}
            className="h-20 w-20 rounded-full border border-muted shadow-sm"
          />
          <CardTitle className="mt-6 text-3xl font-semibold">
            Welcome to {APP_TITLE}
          </CardTitle>
          <CardDescription className="text-base text-muted-foreground">
            Please sign in with your email and password.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={event => setEmail(event.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={event => setPassword(event.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />
            </div>

            {formError ? (
              <Alert variant="destructive">
                <AlertDescription>{formError}</AlertDescription>
              </Alert>
            ) : null}

            <Button
              type="submit"
              size="lg"
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Signing in...
                </span>
              ) : (
                "Sign In"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default Login;
