export interface Product {
    id: string | number;
    name: string;
    brand?: string;
    category?: string;
    priceCents?: number;
    price?: number;
    imageUrl?: string;
    description?: string;
    stock?: number;
    ingredients?: string;
}


