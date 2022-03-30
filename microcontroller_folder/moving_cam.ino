#include <SPI.h>
#include <WiFiNINA.h>
#include <Servo.h>
#include <PubSubClient.h>
#include "secrets.h"

#define ARM_V 2
#define ARM_H 3

WiFiClient mkr1010;
Servo armv;
Servo armh;
void callback(char* topic, byte* payload, unsigned int length);
PubSubClient client(MQTT_BROKER, 1883, callback, mkr1010);

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PW);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi..");
  }
  Serial.print("connected to WiFi\n");
  IPAddress ip = WiFi.localIP();
  Serial.println(ip);
  connect();
  client.setCallback(callback);
  armv.attach(ARM_V);
  armh.attach(ARM_H);
  armh.write(95);
  armv.write(90);
}

void loop() {
  while (!client.connected()) { // zolang ik niet geconnecteerd ben met MQTT, probeer het opnieuw en zodra ik geconnecteerd ben
    connect();
  }
  client.loop();
}

void connect(){
      Serial.println("Connecting to MQTT...");
    if (client.connect(CLIENT_ID, MQTT_USER, MQTT_PW) ){
      Serial.println("connected");
      client.subscribe("camera/move");
    } else {
      Serial.print("failed with state ");
      Serial.print(client.state());
      delay(2000);
    }
}

void callback(char* topic, byte* payload, unsigned int length) {
  switch((char)payload[0]){ 
    case ('u'): move_arm("up",    armv); break;
    case ('d'): move_arm("down",  armv); break;
    case ('l'): move_arm("left",  armh); break;
    case ('r'): move_arm("right", armh); break;
    case ('c'): armh.write(90); armv.write(90); break;
  }
}

void move_arm(String msg, Servo arm) {
  uint8_t value = arm.read();
  Serial.println(value);
  if ((msg == "down") || (msg == "right")) {  // experimenteel bepaald
    if (value) {// value mag ik hier gebruiken (als deze 0 is, word dit gelezen als false) - ik wil namelijk niet dat de arm verder naar negatief gaat als de waarde 0 is (gaat ook niet)
      arm.write(value - 5);
    }
  } else {
    if (value < 180) {
      arm.write(value + 5);
    }
  }
}
