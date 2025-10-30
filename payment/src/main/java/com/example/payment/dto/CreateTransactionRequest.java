package com.example.payment.dto;

import java.math.BigDecimal;

public record CreateTransactionRequest(
    String fromAccountId,
    String toAccountId,
    BigDecimal amount
) {
}