/*
 * =====================================================================================
 * PROJECT: Digital Twin for Predictive Maintenance of Air Conditioner
 * MODULE : Step 1.5 - Unified Multi-Sensor Serial Telemetry
 * =====================================================================================
 * SENSOR PIN MAPPING:
 *   1. DHT11 #1 (Indoor Ambient)      -> GPIO 4 (D4)
 *   2. DHT11 #2 (Outdoor Ambient)     -> GPIO 5 (D5)
 *   3. DS18B20  (Compressor Surface)  -> GPIO 18 (D18) [with 10k ohm pull-up to 3.3V]
 *   4. SW-420   (Vibration Detector)  -> GPIO 19 (D19)
 *   5. MQ135    (Air Quality Index)   -> GPIO 34 (ADC1_CH6)
 * =====================================================================================
 */

#include "DHT.h"
#include <OneWire.h>
#include <DallasTemperature.h>

// Pin Definitions
#define PIN_DHT_INDOOR    4
#define PIN_DHT_OUTDOOR   5
#define PIN_DS18B20       18
#define PIN_SW420         19
#define PIN_MQ135         34

#define DHTTYPE           DHT22

// Sensor Objects
DHT dhtIndoor(PIN_DHT_INDOOR, DHTTYPE);
DHT dhtOutdoor(PIN_DHT_OUTDOOR, DHTTYPE);
OneWire oneWire(PIN_DS18B20);
DallasTemperature ds18b20(&oneWire);

// Timing variables
unsigned long lastReadTime = 0;
const unsigned long READ_INTERVAL = 2000; // 2 seconds

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("===============================================================================");
  Serial.println("         DIGITAL TWIN OF AIR CONDITIONER - HARDWARE TELEMETRY TEST            ");
  Serial.println("===============================================================================");

  // Initialize Sensors
  dhtIndoor.begin();
  dhtOutdoor.begin();
  ds18b20.begin();
  pinMode(PIN_SW420, INPUT);
  analogReadResolution(12);

  Serial.println("[SETUP] All 5 sensors initialized.");
  Serial.println("-------------------------------------------------------------------------------");
  Serial.println("InTemp(C) | InHum(%) | OutTemp(C) | OutHum(%) | CompTemp(C) | Vibration | AQI(%)");
  Serial.println("-------------------------------------------------------------------------------");
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastReadTime >= READ_INTERVAL) {
    lastReadTime = currentMillis;

    // 1. Read DHT11 Sensors
    float inTemp = dhtIndoor.readTemperature();
    float inHum  = dhtIndoor.readHumidity();
    float outTemp = dhtOutdoor.readTemperature();
    float outHum  = dhtOutdoor.readHumidity();

    // 2. Read DS18B20 Compressor Temp
    ds18b20.requestTemperatures();
    float compTemp = ds18b20.getTempCByIndex(0);

    // 3. Read SW-420 Vibration (Digital State)
    int vibState = digitalRead(PIN_SW420);
    String vibStatus = (vibState == HIGH) ? "VIB_ACTIVE" : "NORMAL";

    // 4. Read MQ135 Air Quality (Averaged ADC)
    long mqSum = 0;
    for (int i = 0; i < 10; i++) {
      mqSum += analogRead(PIN_MQ135);
      delay(5);
    }
    int rawMQ = mqSum / 10;
    float aqiPercent = (rawMQ / 4095.0) * 100.0;

    // Print Telemetry Row
    Serial.print(" ");
    if (isnan(inTemp)) Serial.print(" ERR    "); else { Serial.print(inTemp, 1); Serial.print(" C   "); }
    Serial.print("| ");

    if (isnan(inHum)) Serial.print(" ERR    "); else { Serial.print(inHum, 1); Serial.print(" %    "); }
    Serial.print("| ");

    if (isnan(outTemp)) Serial.print(" ERR     "); else { Serial.print(outTemp, 1); Serial.print(" C    "); }
    Serial.print("| ");

    if (isnan(outHum)) Serial.print(" ERR     "); else { Serial.print(outHum, 1); Serial.print(" %     "); }
    Serial.print("| ");

    if (compTemp == DEVICE_DISCONNECTED_C || compTemp == -127.0) {
      Serial.print(" ERR       ");
    } else {
      Serial.print(compTemp, 1); Serial.print(" C     ");
    }
    Serial.print("| ");

    Serial.print(vibStatus);
    if (vibStatus == "NORMAL") Serial.print("    "); else Serial.print(" ");
    Serial.print("| ");

    Serial.print(aqiPercent, 1);
    Serial.println(" %");
  }
}
