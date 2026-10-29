/*
 * =====================================================================================
 * PROJECT: Digital Twin for Predictive Maintenance of Air Conditioner
 * MODULE : Step 1.3 - SW-420 Vibration Sensor Test (Mechanical Shock / Vibration Detection)
 * =====================================================================================
 * WIRING:
 *   SW-420 Module:
 *     - VCC -> ESP32 3.3V (or 5V)
 *     - GND -> ESP32 GND
 *     - DO  -> ESP32 GPIO 19 (D19)
 *
 * NOTE:
 *   The SW-420 is a digital vibration switch / detector. It detects mechanical shocks,
 *   unbalance, or running vibrations. Use the blue onboard potentiometer to adjust sensitivity.
 *   Output is HIGH when idle/open and pulses LOW when vibration occurs (or vice-versa
 *   depending on module variant).
 * =====================================================================================
 */

#define VIBRATION_PIN 19 // GPIO 19 connected to SW-420 DO

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(VIBRATION_PIN, INPUT);

  Serial.println("=================================================");
  Serial.println("   AC DIGITAL TWIN - SW-420 VIBRATION TEST       ");
  Serial.println("=================================================");
  Serial.println("Monitoring GPIO 19 for vibration pulses...");
  Serial.println("Adjust the blue potentiometer if trigger is too sensitive/loose.\n");
}

void loop() {
  // Sampling window: 1000 ms (1 second) to count vibration pulse events
  unsigned long startTime = millis();
  int vibrationTriggers = 0;
  int rawState = 0;

  while (millis() - startTime < 1000) {
    rawState = digitalRead(VIBRATION_PIN);
    // When vibration occurs, switch momentarily flips state
    if (rawState == HIGH) { 
      vibrationTriggers++;
      delay(10); // Simple debounce window
    }
  }

  Serial.println("-------------------------------------------------");
  Serial.print("[VIBRATION] Pulse Count (per sec): ");
  Serial.print(vibrationTriggers);
  Serial.print(" | Status: ");

  if (vibrationTriggers == 0) {
    Serial.println("NORMAL (No Vibration)");
  } else if (vibrationTriggers < 10) {
    Serial.println("DETECTED (Slight Vibration / Normal Operation)");
  } else {
    Serial.println("ALERT (Abnormal Continuous Vibration / Loose Mount or Bearing)");
  }
}
