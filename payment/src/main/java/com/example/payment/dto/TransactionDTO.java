package com.example.payment.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

public record TransactionDTO(
    String id,
    String fromAccountId,
    String toAccountId,
    BigDecimal amount,
    OffsetDateTime createdAt
) {
}