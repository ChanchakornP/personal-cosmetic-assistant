package com.example.payment;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.hamcrest.Matchers;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class TransactionControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void shouldListAccounts() throws Exception {
        mockMvc.perform(get("/api/payment/accounts").accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
            .andExpect(jsonPath("$.length()").value(3))
            .andExpect(jsonPath("$[*].id", Matchers.containsInAnyOrder("1", "2", "3")));
    }

    @Test
    void shouldReturnTransactionWhenIdExists() throws Exception {
        mockMvc.perform(get("/api/payment/transaction/1")
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
            .andExpect(jsonPath("$.id").value("1"))
            .andExpect(jsonPath("$.fromAccountId").value("1"))
            .andExpect(jsonPath("$.toAccountId").value("2"))
            .andExpect(jsonPath("$.amount").value(120.00));
    }

    @Test
    void shouldReturn404WhenTransactionMissing() throws Exception {
        mockMvc.perform(get("/api/payment/transaction/9999")
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isNotFound());
    }

    @Test
    void shouldCreateTransaction() throws Exception {
        String payload = "{" +
            "\"fromAccountId\":\"1\"," +
            "\"toAccountId\":\"2\"," +
            "\"amount\":75.25" +
            "}";

        MvcResult result = mockMvc.perform(post("/api/payment/transaction")
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload)
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isCreated())
            .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
            .andExpect(header().string("Location", Matchers.startsWith("/api/payment/transaction/")))
            .andExpect(jsonPath("$.success").value(true))
            .andExpect(jsonPath("$.message").value("Transaction created"))
            .andExpect(jsonPath("$.transaction.fromAccountId").value("1"))
            .andExpect(jsonPath("$.transaction.toAccountId").value("2"))
            .andExpect(jsonPath("$.transaction.amount").value(75.25))
            .andReturn();

        JsonNode responseBody = objectMapper.readTree(result.getResponse().getContentAsString());
        String transactionId = responseBody.at("/transaction/id").asText();
        assertThat(transactionId).isNotBlank();

        mockMvc.perform(get("/api/payment/transaction/" + transactionId)
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(transactionId))
            .andExpect(jsonPath("$.fromAccountId").value("1"))
            .andExpect(jsonPath("$.toAccountId").value("2"))
            .andExpect(jsonPath("$.amount").value(75.25));
    }

    @Test
    void shouldRejectInvalidTransactionRequest() throws Exception {
        String payload = "{" +
            "\"fromAccountId\":\"1\"," +
            "\"toAccountId\":\"1\"," +
            "\"amount\":-10" +
            "}";

        mockMvc.perform(post("/api/payment/transaction")
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload)
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.success").value(false))
            .andExpect(jsonPath("$.message").exists());
    }
}