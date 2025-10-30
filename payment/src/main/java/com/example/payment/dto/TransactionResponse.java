package com.example.payment.dto;

public record TransactionResponse(
    boolean success,
    String message,
    TransactionDTO transaction
) {
}