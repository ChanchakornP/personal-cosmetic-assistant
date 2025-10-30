package com.example.payment.service;

import com.example.payment.dto.AccountDTO;
import com.example.payment.model.AccountEntity;
import com.example.payment.repository.AccountRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class AccountService {

    private final AccountRepository repository;

    public AccountService(AccountRepository repository) {
        this.repository = repository;
    }

    public List<AccountDTO> findAll() {
        return repository.findAll().stream()
            .map(this::toDto)
            .toList();
    }

    private AccountDTO toDto(AccountEntity entity) {
        return new AccountDTO(String.valueOf(entity.getId()), entity.getBalance());
    }
}