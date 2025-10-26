# Payment

## Data Transfer Object

```ts
// AccountDTO.ts
export interface AccountDTO {
  id: string;        // unique account ID
  balance: number;   // current account balance
}
```

```ts
// TransactionDTO.ts
export interface TransactionDTO {
  id: string;              // unique transaction ID
  fromAccountId: string;   // sender account ID
  toAccountId: string;     // receiver account ID
  amount: number;          // amount transferred
  createdAt?: string;      // optional timestamp
}
```

```ts
// CreateTransactionRequest.ts
export interface CreateTransactionRequest {
  fromAccountId: string;
  toAccountId: string;
  amount: number;
}
```

```ts
// TransactionResponse.ts
export interface TransactionResponse {
  success: boolean;
  message: string;
  transaction?: TransactionDTO;
}
```

## API


| Endpoint                        | Method | Request                    | Response              |
| ------------------------------- | ------ | -------------------------- | --------------------- |
| `/api/payment/accounts`         | GET    | –                          | `AccountDTO[]`        |
| `/api/payment/transaction`      | POST   | `CreateTransactionRequest` | `TransactionResponse` |
| `/api/payment/transaction/{id}` | GET    | –                          | `TransactionDTO`      |
