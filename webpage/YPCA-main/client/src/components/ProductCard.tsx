import { useCart } from "../contexts/CartContext";
import type { Product } from "../types/product";
import { Button } from "./ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "./ui/card";

export default function ProductCard({ product }: { product: Product }) {
    const { addItem } = useCart();

    const price = (product.priceCents ? product.priceCents / 100 : (product.price || 0)).toFixed(2);
    const imageSrc = product.imageUrl || "/logo.svg";

    return (
        <Card className="glass-card">
            <CardHeader>
                <div className="w-full aspect-square overflow-hidden rounded-md bg-muted">
                    {/* eslint-disable-next-line jsx-a11y/alt-text */}
                    <img
                        src={imageSrc}
                        alt={product.name}
                        className="w-full h-full object-cover"
                        loading="lazy"
                        onError={(e) => {
                            const target = e.currentTarget as HTMLImageElement;
                            if (target.src.endsWith("/logo.svg")) return;
                            target.src = "/logo.svg";
                        }}
                    />
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-1">
                    <div className="font-medium leading-tight">{product.name}</div>
                    {product.brand && (
                        <div className="text-xs text-muted-foreground">{product.brand}</div>
                    )}
                    <div className="text-sm text-muted-foreground">${price}</div>
                </div>
            </CardContent>
            <CardFooter>
                <Button className="w-full" onClick={() => addItem(product, 1)}>
                    Add to Cart
                </Button>
            </CardFooter>
        </Card>
    );
}


