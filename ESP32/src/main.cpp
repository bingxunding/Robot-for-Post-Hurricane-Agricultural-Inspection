#include <WiFi.h>
#include <WebServer.h>

// --- Configurazioni Wi-Fi ---
const char* ssid = "ZjLuigi (3)";
const char* password = "12345ciaooo";

// --- Inizializza il server web sulla porta 80 ---
WebServer server(80);

// ---INITIALIZE MOTOR PINS ---///
const int ENA = 3;   
const int IN1 = 4;  
const int IN2 = 2;  

const int ENB = 6;   
const int IN3 = 13; 
const int IN4 = 7;   

int motorSpeed = 255;  
int curvaturePercentage = 20;

void move_forward() {
  digitalWrite(IN1, HIGH);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

void move_backward() {
  digitalWrite(IN1, LOW);     
  digitalWrite(IN2, HIGH);  
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

void turn_left() {
  digitalWrite(IN1, LOW);     
  digitalWrite(IN2, HIGH);  
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

void turn_right() {

  digitalWrite(IN1, HIGH);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

// supposing the rightmotor is ENA
void turn_left_slowly() {

  int internalWheelSpeed = motorSpeed * (100 - curvaturePercentage) / 100;

  digitalWrite(IN1, HIGH);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, internalWheelSpeed);  
  analogWrite(ENB, motorSpeed);
}

// supposing the rightmotor is ENA
void turn_right_slowly() {

  int internalWheelSpeed = motorSpeed * (100 - curvaturePercentage) / 100;

  digitalWrite(IN1, HIGH);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, internalWheelSpeed);

}

void stop_motors() {

  digitalWrite(IN1, LOW);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}

void initialize_HTTP_commands () {
  // --- Definizione degli endpoint (i "comandi" via web)---
  server.on("/forward", []() {
    move_forward();
    server.send(200, "text/plain", "forward");
    Serial.println("Comando ricevuto: forward");
  });
  server.on("/backward", []() {
    move_backward();
    server.send(200, "text/plain", "backward");
    Serial.println("Comando ricevuto: backward");
  });
  server.on("/rotate_right", []() {
    turn_right();
    server.send(200, "text/plain", "rotate_right");
    Serial.println("Comando ricevuto: rotate_right");
  });
  server.on("/rotate_left", []() {
    turn_left();
    server.send(200, "text/plain", "rotate_left");
    Serial.println("Comando ricevuto: rotate_left");
  });
  server.on("/turn_right", []() {
    turn_right_slowly();
    server.send(200, "text/plain", "turn_right");
    Serial.println("Comando ricevuto: turn_right");
  });
  server.on("/turn_left", []() {
    turn_left_slowly();
    server.send(200, "text/plain", "turn_left");
    Serial.println("Comando ricevuto: turn_left");
  });
  server.on("/stop", []() {
    stop_motors();
    server.send(200, "text/plain", "stop");
    Serial.println("Comando ricevuto: stop");
  });
}

void setup() {
  Serial.begin(9600);

  // Connessione al Wi-Fi
  Serial.print("Connessione a ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Connesso! IP: " + WiFi.localIP().toString());

  initialize_HTTP_commands();
  // Avvia il server
  server.begin();
  Serial.println("Server HTTP avviato. In ascolto per comandi...");
}

void loop() {
  server.handleClient(); // Gestisce le richieste HTTP in arrivo
}