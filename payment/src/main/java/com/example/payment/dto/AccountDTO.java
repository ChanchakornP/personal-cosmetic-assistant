package com.example.payment.dto;

import java.math.BigDecimal;

public record AccountDTO(
    String id,
    BigDecimal balance
) {
}