import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { APP_LOGO, APP_TITLE, getLoginUrl } from "@/const";
import { ShoppingCart, User, LayoutDashboard, LogOut } from "lucide-react";
import { Link, useLocation } from "wouter";
import { useCart } from "@/contexts/CartContext";

export default function NavBar() {
    const { user, logout } = useAuth();
    const { items } = useCart();
    const [, setLocation] = useLocation();
    const cartItemCount = items.reduce((sum, i) => sum + i.quantity, 0);

    const handleLogout = async () => {
        await logout();
        setLocation("/");
    };

    return (
        <nav className="glass-nav sticky top-0 z-50">
            <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        {APP_LOGO && (
                            <Link href="/">
                                <img src={APP_LOGO} alt="logo" className="h-8 cursor-pointer" />
                            </Link>
                        )}
                    </div>
                    <Link href="/products">
                        <Button variant="outline" size="sm">Products</Button>
                    </Link>
                </div>
                <div className="flex items-center gap-4">
                    {user ? (
                        <>
                            <Link href="/cart">
                                <Button variant="outline" size="sm" className="relative">
                                    <ShoppingCart className="w-4 h-4 mr-2" />
                                    Cart
                                    {cartItemCount > 0 && (
                                        <span className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                                            {cartItemCount}
                                        </span>
                                    )}
                                </Button>
                            </Link>
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="outline" size="sm">
                                        <User className="w-4 h-4 mr-2" />
                                        {user?.name || "Profile"}
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end" className="w-48">
                                    <DropdownMenuItem onClick={() => setLocation("/")}>
                                        <LayoutDashboard className="w-4 h-4 mr-2" />
                                        Home
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => setLocation("/profile")}>
                                        <User className="w-4 h-4 mr-2" />
                                        Profile
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem onClick={handleLogout}>
                                        <LogOut className="w-4 h-4 mr-2" />
                                        Logout
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </>
                    ) : (
                        <Button onClick={() => (window.location.href = getLoginUrl())}>Sign In</Button>
                    )}
                </div>
            </div>
        </nav>
    );
}


