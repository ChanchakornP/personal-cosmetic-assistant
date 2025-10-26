# Product
Backend (any framework) with APIs. Store database in Supabase (if it possible) and put some mock data

## Schema

```sql
CREATE TABLE Product (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  price DECIMAL(10,2) NOT NULL,
  stock INT DEFAULT 0,
  category VARCHAR(100),
  main_image_url TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## DTO

```ts
export interface ProductDTO {
  id: number;
  name: string;
  description?: string;
  price: number;
  stock: number;
  category?: string;
  mainImageUrl?: string;
  createdAt?: string;
  updatedAt?: string;
}
```

## APIs

|Endpoint|Method|Description|
|---|---|---|
|`/api/products`|GET|List all products|
|`/api/products/:id`|GET|Get one product|
|`/api/products`|POST|Create a new product|
|`/api/products/:id`|PUT|Update product|
|`/api/products/:id`|DELETE|Delete product|
