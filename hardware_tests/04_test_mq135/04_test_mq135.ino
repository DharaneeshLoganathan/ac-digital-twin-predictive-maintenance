/*
 * =====================================================================================
 * PROJECT: Digital Twin for Predictive Maintenance of Air Conditioner
 * MODULE : Step 1.4 - MQ135 Air Quality Sensor Test (Indoor Air Quality / Gas Indicator)
 * =====================================================================================
 * WIRING:
 *   MQ135 Module:
 *     - VCC -> ESP32 5V (VIN / 5V pin - sensor internal heater requires 5V!)
 *     - GND -> ESP32 GND
 *     - AO  -> ESP32 GPIO 34 (ADC1 Channel 6 - 100% safe with Wi-Fi)
 *
 * NOTE:
 *   MQ135 provides an analog voltage corresponding to oxidizable/reducing gases.
 *   Without lab chamber multi-gas calibration, it is presented as a relative
 *   Indoor Air Quality Index (0-100% / Raw ADC 0-4095) rather than absolute CO2 ppm.
 * =====================================================================================
 */

#define MQ135_PIN 34 // GPIO 34 (ADC1_CH6)

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Configure ADC resolution (12-bit: 0 to 4095)
  analogReadResolution(12);

  Serial.println("=================================================");
  Serial.println("   AC DIGITAL TWIN - MQ135 AIR QUALITY TEST      ");
  Serial.println("=================================================");
  Serial.println("Reading analog values from GPIO 34 (ADC1)...");
  Serial.println("Note: MQ135 requires ~2-3 minutes of preheating to stabilize.\n");
}

void loop() {
  delay(2000);

  // Take multiple samples for moving average smoothing
  long sum = 0;
  const int NUM_SAMPLES = 20;
  for (int i = 0; i < NUM_SAMPLES; i++) {
    sum += analogRead(MQ135_PIN);
    delay(10);
  }
  int rawADC = sum / NUM_SAMPLES;

  // Convert to voltage (ESP32 ADC is 3.3V reference)
  float voltage = (rawADC / 4095.0) * 3.3;

  // Calculate Relative Air Quality Index (0% Clean to 100% Highly Polluted)
  // Clean room air typically reads raw ADC 300 - 800
  float aqiPercentage = (rawADC / 4095.0) * 100.0;

  Serial.println("-------------------------------------------------");
  Serial.print("[AIR QUALITY] Raw ADC: ");
  Serial.print(rawADC);
  Serial.print(" / 4095 | Voltage: ");
  Serial.print(voltage, 2);
  Serial.print(" V | Index: ");
  Serial.print(aqiPercentage, 1);
  Serial.print("% | Status: ");

  if (rawADC < 1000) {
    Serial.println("GOOD / CLEAN AIR");
  } else if (rawADC < 2000) {
    Serial.println("MODERATE (Stale air / ventilation recommended)");
  } else {
    Serial.println("POOR / GAS DETECTED (High VOCs/Smoke/Stale Air)");
  }
}
