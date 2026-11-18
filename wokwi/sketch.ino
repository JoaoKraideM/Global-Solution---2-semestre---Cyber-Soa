// SombraViva GS 2026 - ESP32 + DHT22 no Wokwi (simulador)
// Requer backend em execução e Wokwi Private IoT Gateway para host.wokwi.internal.
// NUNCA publique uma chave real ou de produção em repositório aberto.
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHTesp.h>

const int DHT_PIN = 15;
const int LED_PIN = 2;
DHTesp dht;
const char* wifi = "Wokwi-GUEST";
const char* apiUrl = "http://host.wokwi.internal:8000/api/v1/stations/centro-demo/readings";
const char* deviceKey = "COLE_AQUI_O_SENSOR_A_KEY_DO_ENV_APENAS_EM_TESTES";

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  dht.setup(DHT_PIN, DHTesp::DHT22);
  WiFi.begin(wifi, "", 6);
  Serial.print("Conectando");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println(" conectado!");
}

void loop() {
  TempAndHumidity data = dht.getTempAndHumidity();
  if (isnan(data.temperature) || isnan(data.humidity)) {
    Serial.println("Sensor sem leitura");
    delay(2000);
    return;
  }
  String payload = String("{\"temperature_c\":") + String(data.temperature, 1) +
                   ",\"humidity_pct\":" + String(data.humidity, 1) + "}";
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(apiUrl);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Device-Key", deviceKey);
    int status = http.POST(payload);
    Serial.printf("DHT22: %.1f C, %.1f %% | HTTP %d | SIMULADO\n", data.temperature, data.humidity, status);
    digitalWrite(LED_PIN, status == 201 ? HIGH : LOW);
    if (status != 201) Serial.println(http.getString());
    http.end();
  }
  delay(10000);
}
