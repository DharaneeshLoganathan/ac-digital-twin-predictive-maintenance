
#include <WiFi.h>
#include <WebServer.h>

// Wi-Fi credentials
const char* ssid = "Amrita_CHN";
const char* password = "amrita@321";

// LED GPIO pins
#define LED1 4 
#define LED2 5
#define LED3 21

// LED states
bool led1State = false;
bool led2State = false;
bool led3State = false;

// Web server on port 80
WebServer server(80);

// Generate webpage
String getWebPage() {
  String page = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <title>Voice Controlled LEDs</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <style>
    body {
      font-family: Arial;
      text-align: center;
      background: #eef2f7;
      padding: 20px;
    }

    .card {
      background: white;
      padding: 18px;
      margin: 15px auto;
      max-width: 350px;
      border-radius: 12px;
      box-shadow: 0 2px 8px #ccc;
    }

    button {
      padding: 12px 18px;
      margin: 5px;
      border: none;
      border-radius: 6px;
      color: white;
      cursor: pointer;
      font-size: 16px;
    }

    .on { background: #16a34a; }
    .off { background: #dc2626; }
    .voice { background: #2563eb; }

    .state {
      font-weight: bold;
      font-size: 20px;
    }
  </style>
</head>

<body>
  <h1>Voice Controlled LEDs</h1>

  <button class="voice" onclick="startVoice()">
    🎤 Start Voice Command
  </button>

  <p id="status">Click the microphone button and speak.</p>

  <div class="card">
    <h2>LED 1</h2>
    <p class="state" id="s1">{{S1}}</p>
    <button class="on" onclick="control('/led1/on')">ON</button>
    <button class="off" onclick="control('/led1/off')">OFF</button>
  </div>

  <div class="card">
    <h2>LED 2</h2>
    <p class="state" id="s2">{{S2}}</p>
    <button class="on" onclick="control('/led2/on')">ON</button>
    <button class="off" onclick="control('/led2/off')">OFF</button>
  </div>

  <div class="card">
    <h2>LED 3</h2>
    <p class="state" id="s3">{{S3}}</p>
    <button class="on" onclick="control('/led3/on')">ON</button>
    <button class="off" onclick="control('/led3/off')">OFF</button>
  </div>

<script>
function control(url) {
  fetch(url)
    .then(response => {
      if (!response.ok) throw new Error('Request failed');
      return response.text();
    })
    .then(() => location.reload())
    .catch(() => {
      document.getElementById('status').textContent =
        'Cannot communicate with ESP32.';
    });
}

function startVoice() {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    alert('Please use Google Chrome with microphone permission.');
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    document.getElementById('status').textContent = 'Listening...';
  };

  recognition.onerror = event => {
    document.getElementById('status').textContent =
      'Speech error: ' + event.error;
  };

  recognition.onresult = event => {
    const cmd = event.results[0][0].transcript.toLowerCase();
    document.getElementById('status').textContent = 'Heard: ' + cmd;

    let url = '';

    // Check OFF commands before ON commands.
    if (cmd.includes('led one off') ||
        cmd.includes('led 1 off') ||
        cmd.includes('turn off led one') ||
        cmd.includes('turn off led 1') ||
        cmd.includes('light one off')) {
      url = '/led1/off';

    } else if (cmd.includes('led two off') ||
               cmd.includes('led 2 off') ||
               cmd.includes('turn off led two') ||
               cmd.includes('turn off led 2') ||
               cmd.includes('light two off')) {
      url = '/led2/off';

    } else if (cmd.includes('led three off') ||
               cmd.includes('led 3 off') ||
               cmd.includes('turn off led three') ||
               cmd.includes('turn off led 3')) {
      url = '/led3/off';

    } else if (cmd.includes('led one on') ||
               cmd.includes('led 1 on') ||
               cmd.includes('turn on led one') ||
               cmd.includes('turn on led 1') ||
               cmd.includes('light one on')) {
      url = '/led1/on';

    } else if (cmd.includes('led two on') ||
               cmd.includes('led 2 on') ||
               cmd.includes('turn on led two') ||
               cmd.includes('turn on led 2') ||
               cmd.includes('light two on')) {
      url = '/led2/on';

    } else if (cmd.includes('led three on') ||
               cmd.includes('led 3 on') ||
               cmd.includes('turn on led three') ||
               cmd.includes('turn on led 3')) {
      url = '/led3/on';
    }

    if (url === '') {
      document.getElementById('status').textContent =
        'Command not recognized: ' + cmd;
      return;
    }

    fetch(url)
      .then(response => {
        if (!response.ok) throw new Error('Request failed');

        document.getElementById('status').textContent =
          'Executed: ' + cmd;

        setTimeout(() => location.reload(), 500);
      })
      .catch(() => {
        document.getElementById('status').textContent =
          'Connection error. Check Wi-Fi.';
      });
  };

  recognition.start();
}
</script>

</body>
</html>
)rawliteral";

  page.replace("{{S1}}", led1State ? "ON" : "OFF");
  page.replace("{{S2}}", led2State ? "ON" : "OFF");
  page.replace("{{S3}}", led3State ? "ON" : "OFF");

  return page;
}

void setLed(int pin, bool state) {
  digitalWrite(pin, state ? HIGH : LOW);
}

void setup() {
  Serial.begin(115200);

  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);

  // All LEDs initially OFF
  setLed(LED1, false);
  setLed(LED2, false);
  setLed(LED3, false);

  // Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi connected!");
  Serial.print("Open this IP in your browser: http://");
  Serial.println(WiFi.localIP());

  // Homepage
  server.on("/", HTTP_GET, []() {
    server.send(200, "text/html", getWebPage());
  });

  // LED 1
  server.on("/led1/on", HTTP_GET, []() {
    led1State = true;
    setLed(LED1, true);
    server.send(200, "text/plain", "LED 1 ON");
  });

  server.on("/led1/off", HTTP_GET, []() {
    led1State = false;
    setLed(LED1, false);
    server.send(200, "text/plain", "LED 1 OFF");
  });

  // LED 2
  server.on("/led2/on", HTTP_GET, []() {
    led2State = true;
    setLed(LED2, true);
    server.send(200, "text/plain", "LED 2 ON");
  });

  server.on("/led2/off", HTTP_GET, []() {
    led2State = false;
    setLed(LED2, false);
    server.send(200, "text/plain", "LED 2 OFF");
  });

  // LED 3
  server.on("/led3/on", HTTP_GET, []() {
    led3State = true;
    setLed(LED3, true);
    server.send(200, "text/plain", "LED 3 ON");
  });

  server.on("/led3/off", HTTP_GET, []() {
    led3State = false;
    setLed(LED3, false);
    server.send(200, "text/plain", "LED 3 OFF");
  });

  server.begin();
  Serial.println("Web server started!");
}

void loop() {
  server.handleClient();
}
