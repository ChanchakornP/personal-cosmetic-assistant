import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { APP_LOGO, APP_TITLE, getLoginUrl } from "@/const";
import { ShoppingCart } from "lucide-react";
import { Link } from "wouter";
import { useCart } from "@/contexts/CartContext";

export default function NavBar() {
    const { user } = useAuth();
    const { items } = useCart();
    const cartItemCount = items.reduce((sum, i) => sum + i.quantity, 0);

    return (
        <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
            <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        {APP_LOGO && (
                            <Link href="/">
                                <img src={APP_LOGO} alt="logo" className="h-8 cursor-pointer" />
                            </Link>
                        )}
                        <span className="text-xl font-bold text-gray-900">{APP_TITLE}</span>
                    </div>
                    <Link href="/products">
                        <Button variant="outline" size="sm">Products</Button>
                    </Link>
                </div>
                <div className="flex items-center gap-4">
                    {user ? (
                        <>
                            <span className="text-sm text-gray-600">Welcome, {user?.name || "User"}</span>
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
                            <Link href="/profile">
                                <Button variant="outline" size="sm">Profile</Button>
                            </Link>
                        </>
                    ) : (
                        <Button onClick={() => (window.location.href = getLoginUrl())}>Sign In</Button>
                    )}
                </div>
            </div>
        </nav>
    );
}


