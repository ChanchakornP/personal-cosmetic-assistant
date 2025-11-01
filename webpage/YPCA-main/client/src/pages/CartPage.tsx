import { useCart } from "../contexts/CartContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { useLocation } from "wouter";

export default function CartPage() {
    const { items, setQuantity, removeItem, totalCents } = useCart();
    const [, navigate] = useLocation();
    const cartItemCount = items.reduce((sum, item) => sum + item.quantity, 0);

    const goCheckout = () => navigate("/checkout");

    return (
        <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
            {/* Cart Content */}
            <div className="container mx-auto px-4 py-8">
                <h1 className="text-2xl font-semibold mb-6">Shopping Cart</h1>

                {items.length === 0 ? (
                    <div className="text-muted-foreground">Your cart is empty.</div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 space-y-4">
                            {items.map(({ product, quantity }) => {
                                const imageSrc = product.imageUrl || "/logo.svg";
                                return (
                                    <div
                                        key={product.id}
                                        className="flex items-center gap-4 p-4 border rounded-md"
                                    >
                                        <div className="w-20 h-20 rounded bg-muted overflow-hidden flex-shrink-0">
                                            {/* eslint-disable-next-line jsx-a11y/alt-text */}
                                            <img
                                                src={imageSrc}
                                                alt={product.name}
                                                className="w-full h-full object-cover"
                                                onError={(e) => {
                                                    const target = e.currentTarget as HTMLImageElement;
                                                    if (target.src.endsWith("/logo.svg")) return;
                                                    target.src = "/logo.svg";
                                                }}
                                            />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium truncate">{product.name}</div>
                                            {product.brand && (
                                                <div className="text-xs text-muted-foreground">{product.brand}</div>
                                            )}
                                            <div className="text-sm text-muted-foreground">
                                                ${(product.priceCents ? product.priceCents / 100 : (product.price || 0)).toFixed(2)}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Input
                                                type="number"
                                                min={0}
                                                value={quantity}
                                                onChange={(e) =>
                                                    setQuantity(product.id, Math.max(0, Number(e.target.value)))
                                                }
                                                className="w-20"
                                            />
                                            <Button variant="outline" onClick={() => removeItem(product.id)}>
                                                Remove
                                            </Button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        <div className="border rounded-md p-4 h-fit space-y-3">
                            <div className="flex justify-between">
                                <div>Subtotal</div>
                                <div>${(totalCents / 100).toFixed(2)}</div>
                            </div>
                            <Button className="w-full" onClick={goCheckout}>
                                Proceed to Checkout
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}


