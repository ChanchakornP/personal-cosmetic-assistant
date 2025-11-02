import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import Login from "@/pages/Login";
import NotFound from "@/pages/NotFound";
import ProductsPage from "@/pages/ProductsPage";
import CartPage from "@/pages/CartPage";
import Payment from "@/components/Payment";
import { Route, Switch, useLocation } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import FacialAnalysis from "./pages/FacialAnalysis";
import ConflictAnalyzer from "./pages/ConflictAnalyzer";
import Recommendations from "./pages/Recommendations";
import RoutineTracker from "./pages/RoutineTracker";
import Profile from "./pages/Profile";
import NavBar from "./components/NavBar";

function Router() {
  // make sure to consider if you need authentication for certain routes
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/facial-analysis" component={FacialAnalysis} />
      <Route path="/conflict-analyzer" component={ConflictAnalyzer} />
      <Route path="/login" component={Login} />
      <Route path="/recommendations" component={Recommendations} />
      <Route path="/routine-tracker" component={RoutineTracker} />
      <Route path="/profile" component={Profile} />
      <Route path="/products" component={ProductsPage} />
      <Route path="/cart" component={CartPage} />
      <Route path="/checkout" component={Payment} />
      <Route path="/404" component={NotFound} />
      {/* Final fallback route */}
      <Route component={NotFound} />
    </Switch>
  );
}

// NOTE: About Theme
// - First choose a default theme according to your design style (dark or light bg), than change color palette in index.css
//   to keep consistent foreground/background color across components
// - If you want to make theme switchable, pass `switchable` ThemeProvider and use `useTheme` hook

function AppContent() {
  const [location] = useLocation();
  const showNavBar = location !== "/login";

  return (
    <>
      {showNavBar && <NavBar />}
      <Router />
    </>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider
        defaultTheme="light"
      // switchable
      >
        <TooltipProvider>
          <Toaster />
          <AppContent />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
