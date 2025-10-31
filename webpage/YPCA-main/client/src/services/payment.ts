export type AccountDTO = {
    id: string;
    balance: number;
};

export type TransactionResponse = {
    success: boolean;
    message: string;
    transaction: {
        id: string;
        fromAccountId: string;
        toAccountId: string;
        amount: number;
        createdAt?: string;
    } | null;
};

const BASE = (import.meta.env.VITE_PAYMENT_API_URL as string) || "http://localhost:8080/api/payment";

export async function getAccounts(): Promise<AccountDTO[]> {
    const res = await fetch(`${BASE}/accounts`, { credentials: "omit" });
    if (!res.ok) throw new Error(`Failed to fetch accounts (${res.status})`);
    return res.json();
}

export async function createTransaction(params: {
    fromAccountId: string;
    toAccountId: string;
    amount: number; // dollars
}): Promise<TransactionResponse> {
    const res = await fetch(`${BASE}/transaction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            fromAccountId: params.fromAccountId,
            toAccountId: params.toAccountId,
            amount: params.amount,
        }),
    });

    const data = (await res.json()) as TransactionResponse;
    if (!res.ok) {
        throw new Error(data?.message || `Payment failed (${res.status})`);
    }
    if (!data.success) throw new Error(data.message || "Payment failed");
    return data;
}


