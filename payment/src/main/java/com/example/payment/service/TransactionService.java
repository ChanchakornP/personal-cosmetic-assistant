package com.example.payment.service;

import com.example.payment.dto.CreateTransactionRequest;
import com.example.payment.dto.TransactionDTO;
import com.example.payment.model.TransactionEntity;
import com.example.payment.repository.AccountRepository;
import com.example.payment.repository.TransactionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.ZoneId;
import java.util.NoSuchElementException;
import java.util.Optional;

@Service
public class TransactionService {

    private final TransactionRepository transactionRepository;
    private final AccountRepository accountRepository;

    public TransactionService(TransactionRepository transactionRepository,
                              AccountRepository accountRepository) {
        this.transactionRepository = transactionRepository;
        this.accountRepository = accountRepository;
    }

    public Optional<TransactionDTO> findById(String id) {
        Integer transactionId = parseIdentifier(id);
        if (transactionId == null) {
            return Optional.empty();
        }
        return transactionRepository.findById(transactionId)
            .map(this::toDto);
    }

    @Transactional
    public TransactionDTO createTransaction(CreateTransactionRequest request) {
        validateRequest(request);

        Integer fromAccountId = parseAccountIdentifier("fromAccountId", request.fromAccountId());
        Integer toAccountId = parseAccountIdentifier("toAccountId", request.toAccountId());

        accountRepository.findById(fromAccountId)
            .orElseThrow(() -> new NoSuchElementException("Source account not found"));
        accountRepository.findById(toAccountId)
            .orElseThrow(() -> new NoSuchElementException("Destination account not found"));

        TransactionEntity entity = new TransactionEntity();
        entity.setFromAccountId(fromAccountId);
        entity.setToAccountId(toAccountId);
        entity.setAmount(request.amount());

        TransactionEntity saved = transactionRepository.save(entity);
        transactionRepository.flush();

        return transactionRepository.findById(saved.getId())
            .map(this::toDto)
            .orElseThrow(() -> new IllegalStateException("Transaction not found after save"));
    }

    private void validateRequest(CreateTransactionRequest request) {
        if (request == null) {
            throw new IllegalArgumentException("Request body is required");
        }

        BigDecimal amount = request.amount();
        if (request.fromAccountId() == null || request.fromAccountId().isBlank()) {
            throw new IllegalArgumentException("fromAccountId is required");
        }
        if (request.toAccountId() == null || request.toAccountId().isBlank()) {
            throw new IllegalArgumentException("toAccountId is required");
        }
        if (request.fromAccountId().equals(request.toAccountId())) {
            throw new IllegalArgumentException("fromAccountId and toAccountId must be different");
        }
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("amount must be greater than 0");
        }
    }

    private Integer parseIdentifier(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        try {
            return Integer.valueOf(raw);
        } catch (NumberFormatException ex) {
            return null;
        }
    }

    private Integer parseAccountIdentifier(String fieldName, String value) {
        try {
            return Integer.valueOf(value);
        } catch (NumberFormatException ex) {
            throw new IllegalArgumentException(fieldName + " must be a numeric identifier");
        }
    }

    private TransactionDTO toDto(TransactionEntity entity) {
        return new TransactionDTO(
            String.valueOf(entity.getId()),
            String.valueOf(entity.getFromAccountId()),
            String.valueOf(entity.getToAccountId()),
            entity.getAmount(),
            entity.getCreatedAt() == null ? null : entity.getCreatedAt()
                .atZone(ZoneId.systemDefault())
                .toOffsetDateTime()
        );
    }
}