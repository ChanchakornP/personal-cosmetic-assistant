package com.example.payment.controller;

import com.example.payment.dto.CreateTransactionRequest;
import com.example.payment.dto.TransactionDTO;
import com.example.payment.dto.TransactionResponse;
import com.example.payment.service.TransactionService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.util.NoSuchElementException;

@RestController
@RequestMapping("/api/payment/transaction")
public class TransactionController {

    private final TransactionService transactionService;

    public TransactionController(TransactionService transactionService) {
        this.transactionService = transactionService;
    }

    @GetMapping("/{id}")
    public ResponseEntity<TransactionDTO> getTransactionById(@PathVariable String id) {
        return transactionService.findById(id)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<TransactionResponse> createTransaction(@RequestBody CreateTransactionRequest request) {
        try {
            TransactionDTO transaction = transactionService.createTransaction(request);
            TransactionResponse response = new TransactionResponse(true, "Transaction created", transaction);
            return ResponseEntity.created(URI.create("/api/payment/transaction/" + transaction.id()))
                .body(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(new TransactionResponse(false, e.getMessage(), null));
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(new TransactionResponse(false, e.getMessage(), null));
        }
    }
}