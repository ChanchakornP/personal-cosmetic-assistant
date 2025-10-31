import { APP_LOGO, APP_TITLE, getLoginUrl } from "@/const";
import { Button } from "@/components/ui/button";
import DashboardLayout from "@/components/DashboardLayout";

function Login() {
  return (
    <DashboardLayout>
      <div className="flex flex-1 flex-col items-center justify-center gap-6 py-16">
        <img
          src={APP_LOGO}
          alt={`${APP_TITLE} logo`}
          className="h-20 w-20 rounded-full border border-muted shadow-sm"
        />
        <div className="text-center">
          <h1 className="text-3xl font-semibold tracking-tight">
            Welcome to {APP_TITLE}
          </h1>
          <p className="mt-2 text-muted-foreground">
            Sign in to continue exploring personalized cosmetic insights.
          </p>
        </div>
        <Button size="lg" onClick={() => (window.location.href = getLoginUrl())}>
          Continue to Login
        </Button>
      </div>
    </DashboardLayout>
  );
}

export default Login;
