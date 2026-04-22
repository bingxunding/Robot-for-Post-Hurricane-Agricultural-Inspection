#include <Arduino_RouterBridge.h>

void set_led4_color(bool r, bool g, bool b) {
  digitalWrite(LED4_R, r ? LOW : HIGH);
  digitalWrite(LED4_G, g ? LOW : HIGH);
  digitalWrite(LED4_B, b ? LOW : HIGH);
}

void move_forward() {
  set_led4_color(true, false, false);   // rosso
}

void move_backward() {
  set_led4_color(false, true, false);   // verde
}

void turn_left() {
  set_led4_color(false, false, true);   // blu
}

void turn_right() {
  set_led4_color(true, true, false);    // giallo
}

void stop_motors() {
  set_led4_color(false, false, false);  // spento
}

void setup() {
  pinMode(LED4_R, OUTPUT);
  pinMode(LED4_G, OUTPUT);
  pinMode(LED4_B, OUTPUT);

  stop_motors();

  Bridge.begin();

  Bridge.provide("move_forward", move_forward);
  Bridge.provide("move_backward", move_backward);
  Bridge.provide("turn_left", turn_left);
  Bridge.provide("turn_right", turn_right);
  Bridge.provide("stop_motors", stop_motors);
}

void loop() {}