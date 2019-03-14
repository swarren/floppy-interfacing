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

static uint16_t baud = 9600;

void setup()
{
  Serial.begin(baud); // USB is always 12 Mbit/sec
  PORTB = 0xff; // pull-ups
  DDRB = 0; // all input
  PORTC = 0xff; // all high initially
  DDRC = 0xff; // all output
}

static bool wait_out;

void loop()
{
  if (!Serial.available())
    return;

  uint8_t c = Serial.read();
  if (wait_out) {
      PORTC = c;
      wait_out = false;
  } else {
    switch (c) {
    case '=':
      wait_out = true;
      break;
    case '?':
      Serial.write(PINB);
      break;
    default:
      break;
    }
  }
}
