
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <U8g2lib.h>

// ---------- Wi-Fi ----------
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// ---------- OLED ----------
constexpr int OLED_SDA = 21;
constexpr int OLED_SCL = 22;
constexpr uint16_t UDP_PORT = 4210;

// SSD1306 128x64, I2C, full framebuffer
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(
    U8G2_R0,
    U8X8_PIN_NONE
);

WiFiUDP udp;

// 128 * 64 / 8 = 1024 bytes
constexpr size_t FRAME_BYTES = 1024;
constexpr size_t HEADER_BYTES = 4;
constexpr size_t PACKET_BYTES = HEADER_BYTES + FRAME_BYTES;

uint8_t packet[PACKET_BYTES];
uint8_t bitmap[FRAME_BYTES];

unsigned long displayedFrames = 0;
unsigned long lastReport = 0;

void setup() {
  Serial.begin(115200);
  delay(500);

  // Initialize I2C and OLED
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(400000);

  u8g2.setBusClock(400000);
  u8g2.begin();
  u8g2.clearBuffer();

  u8g2.setFont(u8g2_font_6x10_tf);
  u8g2.drawStr(0, 18, "OLED Video Stream");
  u8g2.drawStr(0, 34, "Connecting WiFi...");
  u8g2.sendBuffer();

  // Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  // Start UDP receiver
  if (udp.begin(UDP_PORT) == 1) {
    Serial.print("UDP listening on port ");
    Serial.println(UDP_PORT);
  } else {
    Serial.println("Failed to start UDP");
  }

  u8g2.clearBuffer();
  u8g2.drawStr(0, 18, "Waiting for video");
  u8g2.drawStr(0, 34, "Port: 4210");
  u8g2.sendBuffer();
}

void loop() {
  int packetSize = udp.parsePacket();

  if (packetSize == PACKET_BYTES) {
    int received = udp.read(packet, sizeof(packet));

    if (received == PACKET_BYTES) {
      // The first four bytes are the sequence number.
      // The remaining 1024 bytes are the XBM bitmap.
      memcpy(bitmap, packet + HEADER_BYTES, FRAME_BYTES);

      // Draw the complete frame.
      u8g2.clearBuffer();
      u8g2.drawXBMP(0, 0, 128, 64, bitmap);
      u8g2.sendBuffer();

      displayedFrames++;
    }
  } else if (packetSize > 0) {
    // Discard packets that do not match our protocol.
    while (udp.available()) {
      udp.read();
    }
  }

  // Report the display update rate once per second.
  unsigned long now = millis();

  if (now - lastReport >= 1000) {
    Serial.printf("Displayed frames/sec: %lu\n",
                  displayedFrames);
    displayedFrames = 0;
    lastReport = now;
  }
}
