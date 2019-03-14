/*
 * Copyright 2019 Stephen Warren <swarren@wwwdotorg.org>
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */ 

#define BIT(x) (1 << (x))

#define DRIVE_SEL_B BIT(0)
#define MOTOR_EN_B  BIT(1)
#define DIRECTION   BIT(2)
#define STEP        BIT(3)
#define HEAD        BIT(4)

#define TRACK0      BIT(4)
#define WRITE_PROT  BIT(5)
#define CHANGE_RDY  BIT(6)

uint8_t oval;

void setup()
{
    PORTB = 0xff; // pull-ups
    DDRB = 0; // all input
    PORTC = 0xff; // all high initially
    DDRC = 0xff; // all output

    oval = 0xff;
    oval &= ~DRIVE_SEL_B;
    PORTC = oval;

    oval |= DIRECTION;
    PORTC = oval;
    for (int i = 0; i < 80; i++) {
        if (!(PORTB & TRACK0))
            break;
        oval &= ~STEP;
        PORTC = oval;
        delay(1);
        oval |= STEP;
        PORTC = oval;
        delay(3);
    }
    oval &= ~DIRECTION;
    PORTC = oval;
}

static int track;
static int step_dir;

static void note(uint16_t period_us, uint16_t duration_ms)
{
    uint16_t steps = (uint32_t(duration_ms) * 1000) / period_us;

    for (uint16_t i = 0; i < steps; i++) {
        oval &= ~STEP;
        PORTC = oval;
        delayMicroseconds(250);
        oval |= STEP;
        PORTC = oval;
        delayMicroseconds(period_us - 250);
        track += step_dir;
        if (track == 0) {
            step_dir = 1;
            oval &= ~DIRECTION;
            PORTC = oval;
        } else if (track == 79) {
            step_dir = -1;
            oval |= DIRECTION;
            PORTC = oval;
        }
    }
}

#define E4 uint16_t(1000000 / 329.628)
#define D4 uint16_t(1000000 / 293.665)
#define C4 uint16_t(1000000 / 261.626)
#define B3 uint16_t(1000000 / 246.942)
#define A3 uint16_t(1000000 / 220)
#define G3 uint16_t(1000000 / 195.998)
#define F3S uint16_t(1000000 / 184.997)

#define CROTCHET       450
#define QUAVER         225

#define NOTE(pitch, duration) {pitch, duration, 150}

static const struct {
    uint16_t period_us;
    uint16_t duration_ms;
    uint16_t delay_ms;
} notes[] = {
    NOTE(G3, CROTCHET),
    NOTE(G3, CROTCHET),
    NOTE(A3, CROTCHET),

    NOTE(F3S, CROTCHET + QUAVER),
    NOTE(G3, QUAVER),
    NOTE(A3, CROTCHET),

    NOTE(B3, CROTCHET),
    NOTE(B3, CROTCHET),
    NOTE(C4, CROTCHET),

    NOTE(B3, CROTCHET + QUAVER),
    NOTE(A3, QUAVER),
    NOTE(G3, CROTCHET),

    NOTE(A3, CROTCHET),
    NOTE(G3, CROTCHET),
    NOTE(F3S, CROTCHET),

    NOTE(G3, CROTCHET),
    NOTE(G3, QUAVER),
    NOTE(A3, QUAVER),
    NOTE(B3, QUAVER),
    NOTE(C4, QUAVER),

    NOTE(D4, CROTCHET),
    NOTE(D4, CROTCHET),
    NOTE(D4, CROTCHET),

    NOTE(D4, CROTCHET + QUAVER),
    NOTE(C4, QUAVER),
    NOTE(B3, CROTCHET),

    NOTE(C4, CROTCHET),
    NOTE(C4, CROTCHET),
    NOTE(C4, CROTCHET),

    NOTE(C4, CROTCHET + QUAVER),
    NOTE(B3, QUAVER),
    NOTE(A3, CROTCHET),

    NOTE(B3, CROTCHET),
    NOTE(C4, QUAVER),
    NOTE(B3, QUAVER),
    NOTE(A3, QUAVER),
    NOTE(G3, QUAVER),

    NOTE(B3, CROTCHET + QUAVER),
    NOTE(C4, QUAVER),
    NOTE(D4, CROTCHET),

    NOTE(E4, QUAVER),
    NOTE(C4, QUAVER),
    NOTE(B3, CROTCHET),
    NOTE(A3, CROTCHET),

    NOTE(G3, CROTCHET * 3),
};
#define ARSIZE(x) (sizeof(x) / sizeof((x)[0]))

void loop()
{
    for (uint16_t i = 0; i < ARSIZE(notes); i++) {
        note(notes[i].period_us, notes[i].duration_ms);
        delay(notes[i].delay_ms);
    }

    delay(2500);
}
