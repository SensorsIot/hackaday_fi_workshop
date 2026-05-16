#include <stm8s.h>
#include <stdint.h>
#include <stdio.h>

#define F_CPU       2000000UL
#define BAUDRATE    115200

static void uart_init() {
    uint16_t div = (F_CPU + BAUDRATE / 2) / BAUDRATE;
    UART1_BRR2 = ((div >> 8) & 0xF0) + (div & 0x0F);
    UART1_BRR1 = div >> 4;
    UART1_CR2 = (1 << UART1_CR2_TEN) | (1 << UART1_CR2_REN);
}

static void uart_write(uint8_t data) {
    UART1_DR = data;
    while (!(UART1_SR & (1 << UART1_SR_TC)));
}

int putchar(int c) {
    uart_write(c);
    return 0;
}

void main() {
    PD_DDR |= 1 << 4;
    PD_CR1 |= 1 << 4;
    PD_ODR |= 1 << 4;

    uart_init();

    uint32_t it = 0;
    for (;;) {
        volatile uint32_t ctr, i, j;
        ctr = 0;
        for (i = 0; i < 100; i++) {
            for (j = 0; j < 200; j++) {
                ctr++;
            }
        }
        printf("[%lu][%lu][%lu]: %lu\r\n", i, j, ctr, it);
        it++;
    }
}

