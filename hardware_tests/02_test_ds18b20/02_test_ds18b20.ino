/*
 * =====================================================================================
 * PROJECT: Digital Twin for Predictive Maintenance of Air Conditioner
 * MODULE : Step 1.2 - DS18B20 Waterproof Temperature Sensor Test (Compressor Temp)
 * =====================================================================================
 * WIRING:
 *   DS18B20 Sensor (Standard 3-wire: Red/VCC, Black/GND, Yellow/DATA):
 *     - RED (VCC)    -> ESP32 3.3V
 *     - BLACK (GND)  -> ESP32 GND
 *     - YELLOW (DATA)-> ESP32 GPIO 18 (D18)
 *     - RESISTOR     -> Connect 10k ohm (or 4.7k ohm) resistor BETWEEN DATA (Yellow)
 *                       and 3.3V (Red) as a PULL-UP resistor! (CRITICAL)
 *
 * REQUIRED ARDUINO LIBRARIES:
 *   1. "OneWire" by Jim Studt, Tom Pollard, Robin Bliss, Paul Stoffregen
 *   2. "DallasTemperature" by Miles Burton
 * =====================================================================================
 */

#include <OneWire.h>
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 18 // GPIO 18 for DS18B20 Data Line

// Setup a oneWire instance to communicate with any OneWire devices
OneWire oneWire(ONE_WIRE_BUS);

// Pass our oneWire reference to Dallas Temperature sensor
DallasTemperature sensors(&oneWire);

// Device address storage
DeviceAddress compressorThermometer;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("=================================================");
  Serial.println("   AC DIGITAL TWIN - DS18B20 COMPRESSOR TEMP     ");
  Serial.println("=================================================");
  Serial.println("Locating DS18B20 sensor on GPIO 18...");

  sensors.begin();
  
  int deviceCount = sensors.getDeviceCount();
  Serial.print("Found ");
  Serial.print(deviceCount);
  Serial.println(" OneWire device(s).");

  if (deviceCount == 0) {
    Serial.println("[WARNING] No DS18B20 detected!");
    Serial.println("          1. Check that DATA is on GPIO 18.");
    Serial.println("          2. Ensure 10k/4.7k ohm pull-up resistor is between DATA & 3.3V.");
  } else {
    if (sensors.getAddress(compressorThermometer, 0)) {
      Serial.print("Device 0 Address: ");
      for (uint8_t i = 0; i < 8; i++) {
        if (compressorThermometer[i] < 16) Serial.print("0");
        Serial.print(compressorThermometer[i], HEX);
      }
      Serial.println();
      sensors.setResolution(compressorThermometer, 11); // 11-bit resolution (0.125°C step, ~375ms conversion)
    }
  }
  Serial.println("\nStarting temperature readings...\n");
}

void loop() {
  delay(1500);

  sensors.requestTemperatures(); // Send the command to get temperatures
  float compTemp = sensors.getTempCByIndex(0);

  Serial.println("-------------------------------------------------");
  // Check for error codes
  if (compTemp == DEVICE_DISCONNECTED_C || compTemp == -127.00) {
    Serial.println("[ERROR] DS18B20 Disconnected or reading -127.00 °C!");
    Serial.println("        Verify the 10k ohm pull-up resistor between GPIO 18 and 3.3V.");
  } else if (compTemp == 85.00) {
    Serial.println("[WARNING] Reading 85.00 °C (Power-on reset default before read completed).");
  } else {
    Serial.print("[COMPRESSOR] Temp: ");
    Serial.print(compTemp, 2);
    Serial.print(" °C (");
    Serial.print((compTemp * 9.0 / 5.0) + 32.0, 1);
    Serial.println(" °F)");

    // Threshold indicator
    if (compTemp > 65.0) {
      Serial.println("[ALERT] Compressor High Temperature Warning!");
    } else if (compTemp > 75.0) {
      Serial.println("[CRITICAL] Compressor Overheating Danger!");
    } else {
      Serial.println("[STATUS] Compressor Temperature Normal.");
    }
  }
}
