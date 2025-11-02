import { useCart } from "../contexts/CartContext";
import { Button } from "./ui/button";
import { useLocation } from "wouter";
import { useMutation } from "@tanstack/react-query";
import { createTransaction } from "../services/payment";
import { useState, useMemo } from "react";
import { Input } from "./ui/input";
import { toast } from "sonner";

export default function Payment() {
    const { totalCents, clear, items } = useCart();
    const [, navigate] = useLocation();

    const amountDollars = useMemo(() => Math.max(0, totalCents) / 100, [totalCents]);
    const STORE_ACCOUNT_ID = (import.meta.env.VITE_STORE_ACCOUNT_ID as string) || "1";
    const [fromAccountId, setFromAccountId] = useState<string>("");

    const payMutation = useMutation({
        mutationFn: () =>
            createTransaction({ fromAccountId: String(fromAccountId), toAccountId: STORE_ACCOUNT_ID, amount: amountDollars }),
        onSuccess: () => {
            toast.success("Payment successful");
            clear();
            navigate("/products");
        },
        onError: (err: unknown) => {
            const msg = err instanceof Error ? err.message : "Payment failed";
            toast.error(msg);
        },
    });

    const handleConfirm = () => {
        if (!fromAccountId) {
            toast.error("Enter your account ID");
            return;
        }
        payMutation.mutate();
    };

    if (items.length === 0) {
        return (
            <div className="min-h-screen">
                <div className="container mx-auto px-4 py-8">
                    <h1 className="text-2xl font-semibold mb-6">Checkout</h1>
                    <div>Your cart is empty.</div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen">
            <div className="container mx-auto px-4 py-8">
                <h1 className="text-2xl font-semibold mb-6">Checkout</h1>
                <div className="max-w-md border rounded-md p-4 space-y-4">
                    <div className="flex justify-between">
                        <div>Total</div>
                        <div className="font-medium">${amountDollars.toFixed(2)}</div>
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-medium">From Account ID</label>
                        <Input
                            placeholder="Enter your account id (e.g. 1)"
                            value={fromAccountId}
                            onChange={(e) => setFromAccountId(e.target.value)}
                            inputMode="numeric"
                        />
                    </div>
                    <div className="space-y-1 text-sm text-muted-foreground">
                        <div>To Account (store): #{STORE_ACCOUNT_ID}</div>
                    </div>

                    <Button className="w-full" onClick={handleConfirm} disabled={payMutation.isPending}>
                        {payMutation.isPending ? "Processing..." : "Confirm and Pay"}
                    </Button>
                </div>
            </div>
        </div>
    );
}


