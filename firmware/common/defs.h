#ifndef __DEFS_H__
#define  __DEFS_H__

#if F_CPU == 16000000UL
#define    TIMER1_INIT      0xFFEF
#define    TIMER1_FLAGS     _BV(CS12)|(1<<CS10); // 16Mhz / 1024 / 16 = .001024 per tick
#else
#define    TIMER1_INIT      0xFFF7
#define    TIMER1_FLAGS     _BV(CS12)|(1<<CS10); // 8Mhz / 1024 / 8 = .001024 per tick
#endif

// Bit manipulation macros
#define sbi(a, b) ((a) |= 1 << (b))       //sets bit B in variable A
#define cbi(a, b) ((a) &= ~(1 << (b)))    //clears bit B in variable A
#define tbi(a, b) ((a) ^= 1 << (b))       //toggles bit B in variable A

#define max(a, b) ((a) > (b) ? (a) : (b))
#define min(a, b) ((a) < (b) ? (a) : (b))

#endif
