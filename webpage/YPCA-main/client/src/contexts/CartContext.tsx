import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { Product } from "../types/product";

export type CartItem = { product: Product; quantity: number };
export type CartState = { items: CartItem[] };

type CartContextValue = {
    items: CartItem[];
    addItem: (product: Product, quantity?: number) => void;
    removeItem: (productId: string) => void;
    setQuantity: (productId: string, quantity: number) => void;
    clear: () => void;
    totalCents: number;
};

const CartContext = createContext<CartContextValue | undefined>(undefined);

const STORAGE_KEY = "pca-cart";

function loadInitialCart(): CartItem[] {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) return [];
        return parsed;
    } catch {
        return [];
    }
}

export function CartProvider({ children }: { children: React.ReactNode }) {
    const [items, setItems] = useState<CartItem[]>(loadInitialCart);

    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
        } catch {
            // ignore storage errors
        }
    }, [items]);

    const addItem = useCallback((product: Product, quantity: number = 1) => {
        setItems((prev) => {
            const idx = prev.findIndex((i) => i.product.id === product.id);
            if (idx >= 0) {
                const next = [...prev];
                next[idx] = { ...next[idx], quantity: next[idx].quantity + quantity };
                return next;
            }
            return [...prev, { product, quantity }];
        });
    }, []);

    const removeItem = useCallback((productId: string) => {
        setItems((prev) => prev.filter((i) => i.product.id !== productId));
    }, []);

    const setQuantity = useCallback((productId: string, quantity: number) => {
        setItems((prev) => {
            if (quantity <= 0) return prev.filter((i) => i.product.id !== productId);
            return prev.map((i) => (i.product.id === productId ? { ...i, quantity } : i));
        });
    }, []);

    const clear = useCallback(() => setItems([]), []);

    const totalCents = useMemo(
        () => items.reduce((sum, i) => sum + i.product.priceCents * i.quantity, 0),
        [items]
    );

    const value = useMemo(
        () => ({ items, addItem, removeItem, setQuantity, clear, totalCents }),
        [items, addItem, removeItem, setQuantity, clear, totalCents]
    );

    return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
    const ctx = useContext(CartContext);
    if (!ctx) throw new Error("useCart must be used within CartProvider");
    return ctx;
}


