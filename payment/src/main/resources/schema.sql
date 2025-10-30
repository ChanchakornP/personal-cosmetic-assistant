DROP TABLE IF EXISTS "Transaction";
DROP TABLE IF EXISTS "Account";

CREATE TABLE "Account" (
    id SERIAL PRIMARY KEY,
    balance NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "Transaction" (
    id SERIAL PRIMARY KEY,
    from_account_id INT NOT NULL,
    to_account_id INT NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_amount_positive CHECK (amount > 0),
    CONSTRAINT ck_accounts_distinct CHECK (from_account_id <> to_account_id),
    CONSTRAINT fk_tx_from_account FOREIGN KEY (from_account_id) REFERENCES "Account"(id) ON DELETE CASCADE,
    CONSTRAINT fk_tx_to_account FOREIGN KEY (to_account_id) REFERENCES "Account"(id) ON DELETE CASCADE
);

CREATE INDEX idx_tx_from_account ON "Transaction" (from_account_id);
CREATE INDEX idx_tx_to_account ON "Transaction" (to_account_id);
CREATE INDEX idx_tx_created_at ON "Transaction" (created_at);


