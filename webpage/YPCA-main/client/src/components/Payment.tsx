import { useCart } from "../contexts/CartContext";
import { Button } from "./ui/button";
import { useLocation } from "wouter";
import NavBar from "@/components/NavBar";

export default function Payment() {
    const { totalCents, clear, items } = useCart();
    const [, navigate] = useLocation();

    const handleConfirm = () => {
        // Simple checkout confirmation, no external gateway
        clear();
        navigate("/products");
    };

    if (items.length === 0) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
                <NavBar />
                <div className="container mx-auto px-4 py-8">
                    <h1 className="text-2xl font-semibold mb-6">Checkout</h1>
                    <div>Your cart is empty.</div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
            <NavBar />
            <div className="container mx-auto px-4 py-8">
                <h1 className="text-2xl font-semibold mb-6">Checkout</h1>
                <div className="max-w-md border rounded-md p-4 space-y-4">
                    <div className="flex justify-between">
                        <div>Total</div>
                        <div className="font-medium">${(totalCents / 100).toFixed(2)}</div>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        This is a simplified checkout. Click confirm to place your order.
                    </p>
                    <Button className="w-full" onClick={handleConfirm}>
                        Confirm and Pay
                    </Button>
                </div>
            </div>
        </div>
    );
}


