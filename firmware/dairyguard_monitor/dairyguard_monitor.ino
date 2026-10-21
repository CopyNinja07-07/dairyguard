/* DairyGuard Kinetic on an ESP32 with a DS18B20 probe.
 *
 * Wiring: DS18B20 data to GPIO 4 with a 4.7 kOhm pull-up to 3.3 V; status LEDs on GPIO 25 (green), 26 (amber), 27 (red).
 * Libraries: OneWire, DallasTemperature (Arduino Library Manager).
 * Every 15 minutes the probe is read, the monitor is updated, and one line is printed over serial:
 *   hours, temperature, shelf life used, chance crossed, hours left at 4 C (typical, cautious), state
 * The kinetic core (dg_core.c) is tested on a desktop against the Python reference: see tests/test_firmware.py. */
#include <OneWire.h>
#include <DallasTemperature.h>
extern "C" {
#include "dg_core.h"
}

const int PIN_PROBE = 4, PIN_GREEN = 25, PIN_AMBER = 26, PIN_RED = 27;
const unsigned long PERIOD_MS = 15UL * 60UL * 1000UL;
const char *STATE[] = {"fresh", "use soon", "check before use", "likely over the limit"};

OneWire wire(PIN_PROBE);
DallasTemperature probe(&wire);
dg_monitor mon;
unsigned long last = 0;

void show(uint8_t st) {
  digitalWrite(PIN_GREEN, st == 0); digitalWrite(PIN_AMBER, st == 1 || st == 2); digitalWrite(PIN_RED, st == 3);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_GREEN, OUTPUT); pinMode(PIN_AMBER, OUTPUT); pinMode(PIN_RED, OUTPUT);
  probe.begin();
  dg_init(&mon, &DG_MILK, 20261021u);
  Serial.println("hours,temp_c,shelf_life_used,chance_crossed,hours_left_4c,hours_left_4c_cautious,state");
  last = millis() - PERIOD_MS;
}

void loop() {
  if (millis() - last < PERIOD_MS) { delay(200); return; }
  last += PERIOD_MS;
  probe.requestTemperatures();
  float T = probe.getTempCByIndex(0);
  if (T == DEVICE_DISCONNECTED_C) { Serial.println("probe not found"); return; }
  dg_update(&mon, T, PERIOD_MS / 3600000.0f);
  dg_status s = dg_status_now(&mon);
  show(s.state);
  Serial.printf("%.2f,%.2f,%.3f,%.2f,%.1f,%.1f,%s\n", mon.hours, T, s.shelf_life_used, s.probability_crossed,
                s.hours_left_4C, s.hours_left_4C_cautious, STATE[s.state]);
}
