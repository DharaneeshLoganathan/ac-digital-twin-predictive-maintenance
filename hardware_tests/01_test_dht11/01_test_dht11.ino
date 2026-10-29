/*
 * =====================================================================================
 * PROJECT: Digital Twin for Predictive Maintenance of Air Conditioner
 * MODULE : Step 1.1 - DHT11 Dual Sensor Test (Indoor & Outdoor)
 * =====================================================================================
 * WIRING:
 *   DHT11 #1 (Indoor):
 *     - VCC  -> ESP32 3.3V (or 5V for module with built-in regulator)
 *     - GND  -> ESP32 GND
 *     - DATA -> ESP32 GPIO 4 (D4)
 *
 *   DHT11 #2 (Outdoor):
 *     - VCC  -> ESP32 3.3V (or 5V for module with built-in regulator)
 *     - GND  -> ESP32 GND
 *     - DATA -> ESP32 GPIO 5 (D5)
 *
 * REQUIRED ARDUINO LIBRARIES:
 *   1. "DHT sensor library" by Adafruit
 *   2. "Adafruit Unified Sensor" by Adafruit
 * =====================================================================================
 */

#include "DHT.h"

#define DHTPIN_INDOOR   4     // GPIO 4 connected to Indoor DHT11
#define DHTPIN_OUTDOOR  5     // GPIO 5 connected to Outdoor DHT11
#define DHTTYPE         DHT22 // Sensor Type

DHT dhtIndoor(DHTPIN_INDOOR, DHTTYPE);
DHT dhtOutdoor(DHTPIN_OUTDOOR, DHTTYPE);

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("=================================================");
  Serial.println("   AC DIGITAL TWIN - DHT11 DUAL SENSOR TEST      ");
  Serial.println("=================================================");
  Serial.println("Initializing DHT11 sensors...");
  
  dhtIndoor.begin();
  dhtOutdoor.begin();
  
  Serial.println("Sensors initialized. Starting readings...\n");
}

void loop() {
  // DHT11 requires at least 1.5 - 2 seconds between readings
  delay(2000);

  float indoorTemp = dhtIndoor.readTemperature();
  float indoorHum  = dhtIndoor.readHumidity();

  float outdoorTemp = dhtOutdoor.readTemperature();
  float outdoorHum  = dhtOutdoor.readHumidity();

  Serial.println("-------------------------------------------------");
  
  // Validate Indoor Readings
  if (isnan(indoorTemp) || isnan(indoorHum)) {
    Serial.println("[ERROR] Failed to read from Indoor DHT11 on GPIO 4!");
    Serial.println("        Troubleshoot: Check VCC, GND, and DATA pin connection.");
  } else {
    Serial.print("[INDOOR ] Temp: ");
    Serial.print(indoorTemp, 1);
    Serial.print(" °C  |  Humidity: ");
    Serial.print(indoorHum, 1);
    Serial.println(" %");
  }

  // Validate Outdoor Readings
  if (isnan(outdoorTemp) || isnan(outdoorHum)) {
    Serial.println("[ERROR] Failed to read from Outdoor DHT11 on GPIO 5!");
    Serial.println("        Troubleshoot: Check VCC, GND, and DATA pin connection.");
  } else {
    Serial.print("[OUTDOOR] Temp: ");
    Serial.print(outdoorTemp, 1);
    Serial.print(" °C  |  Humidity: ");
    Serial.print(outdoorHum, 1);
    Serial.println(" %");
  }

  // Cooling Temperature Delta (Outdoor - Indoor)
  if (!isnan(indoorTemp) && !isnan(outdoorTemp)) {
    float tempDelta = outdoorTemp - indoorTemp;
    Serial.print("[DELTA  ] Outdoor - Indoor Delta: ");
    Serial.print(tempDelta, 1);
    Serial.println(" °C");
  }
}
