/* Cycle count of one key schedule on an ATmega328P (simavr): Timer1, prescaler 1, result sent over the UART. */
#include <avr/io.h>
#include <stdint.h>
void ks_std(const uint16_t*, uint16_t*); void ks_v3(const uint16_t*, uint16_t*); void ks_null(const uint16_t*, uint16_t*);
static void put(char c){ while(!(UCSR0A&(1<<UDRE0))); UDR0=c; }
static void num(uint16_t v){ char b[6]; int8_t i=0; do{ b[i++]='0'+v%10; v/=10; }while(v); while(i--) put(b[i]); put('\n'); }
static uint16_t run(void (*f)(const uint16_t*, uint16_t*), const uint16_t *mk){ static uint16_t rk[32]; uint16_t a,b; TCNT1=0; a=TCNT1; f(mk,rk); b=TCNT1; return b-a; }
int main(void){ static const uint16_t K[3][4]={{0x0100,0x0908,0x1110,0x1918},{0xFFFF,0xFFFF,0xFFFF,0xFFFF},{0x1234,0xABCD,0x0F0F,0x8001}};
    UBRR0=0; UCSR0B=(1<<TXEN0); TCCR1A=0; TCCR1B=1;
    for(uint8_t k=0;k<3;k++){ num(run(ks_null,K[k])); num(run(ks_std,K[k])); num(run(ks_v3,K[k])); }
    put('E'); for(;;); }
