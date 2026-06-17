#include <WiFi.h>
#include <WebServer.h>

// --- Configurazioni Wi-Fi ---
const char* ssid = "ZjLuigi (3)";
const char* password = "12345ciaooo";

// --- Inizializza il server web sulla porta 80 ---
WebServer server(80);

// ---INITIALIZE MOTOR PINS ---///
const int ENA = 13;   
const int IN1 = 12;  
const int IN2 = 14;  

const int ENB = 27;   
const int IN3 = 26; 
const int IN4 = 25;   

// PWM configuration
#define PWM_FREQ 500        // 500 Hz for reliable low speeds
#define PWM_RES 8           // 8-bit resolution (0-255)

// Define PWM channels
const int pwmChannelA = 0;
const int pwmChannelB = 1;

int motorSpeed = 255;  
int curvaturePercentage = 100;

void move_forward() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  ledcWrite(pwmChannelA, motorSpeed);
  ledcWrite(pwmChannelB, motorSpeed);
}

void move_backward() {
  digitalWrite(IN1, LOW);     
  digitalWrite(IN2, HIGH);  
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  ledcWrite(pwmChannelA, motorSpeed);
  ledcWrite(pwmChannelB, motorSpeed);
}

void turn_left() {
  digitalWrite(IN1, LOW);     
  digitalWrite(IN2, HIGH);  
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  ledcWrite(pwmChannelA, motorSpeed);
  ledcWrite(pwmChannelB, motorSpeed);
}

void turn_right() {

  digitalWrite(IN1, HIGH);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  ledcWrite(pwmChannelA, motorSpeed);
  ledcWrite(pwmChannelB, motorSpeed);
}

// supposing the rightmotor is ENA
// Gentle left turn: left motor slower, right motor full speed
void turn_left_slowly() {
  int leftSpeed = motorSpeed * (100 - curvaturePercentage) / 100;
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  ledcWrite(pwmChannelA, motorSpeed);   // left slower
  ledcWrite(pwmChannelB, leftSpeed);  // right full
}

// Gentle right turn: right motor slower, left motor full speed
void turn_right_slowly() {
  int rightSpeed = motorSpeed * (100 - curvaturePercentage) / 100;
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  ledcWrite(pwmChannelA, rightSpeed);  // left full
  ledcWrite(pwmChannelB, motorSpeed);  // right slower
}

void stop_motors() {

  digitalWrite(IN1, LOW);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  ledcWrite(pwmChannelA, 0); 
  ledcWrite(pwmChannelB, 0);

}
void initialize_HTTP_commands () {
  // --- Definizione degli endpoint (i "comandi" via web)---
  server.on("/on", []() {
    Serial.println("Comando ricevuto: ON");
    server.send(200, "text/plain", "on");
  });
  server.on("/forward", []() {
    Serial.println("Comando ricevuto: forward");
    move_forward();
    server.send(200, "text/plain", "forward");
  });
  server.on("/backward", []() {
    Serial.println("Comando ricevuto: backward");
    move_backward();
    server.send(200, "text/plain", "backward");
  });
  server.on("/rotate_right", []() {
    Serial.println("Comando ricevuto: rotate_right");
    turn_right();
    server.send(200, "text/plain", "rotate_right");
  });
  server.on("/rotate_left", []() {
    Serial.println("Comando ricevuto: rotate_left");
    turn_left();
    server.send(200, "text/plain", "rotate_left");
  });
  server.on("/turn_right", []() {
    Serial.println("Comando ricevuto: turn_right");
    turn_right_slowly();
    server.send(200, "text/plain", "turn_right");
  });
  server.on("/turn_left", []() {
    Serial.println("Comando ricevuto: turn_left");
    turn_left_slowly();
    server.send(200, "text/plain", "turn_left");
  });
  server.on("/stop", []() {
    Serial.println("Comando ricevuto: stop");
    stop_motors();
    server.send(200, "text/plain", "stop");
  });
  server.on("/setspeed", []() {
  if (server.hasArg("value")) {
    int newSpeed = server.arg("value").toInt();
    // Clamp between 0 and 255
    if (newSpeed < 0) newSpeed = 0;
    if (newSpeed > 255) newSpeed = 255;
    motorSpeed = newSpeed;
    Serial.print("Motor speed set to: ");
    Serial.println(motorSpeed);
    server.send(200, "text/plain", "Speed set to " + String(motorSpeed));
  } else {
    server.send(400, "text/plain", "Missing 'value' parameter");
  }
});

server.on("/setcurvature", []() {
  if (server.hasArg("value")) {
    int newCurve = server.arg("value").toInt();
    // Clamp between 0 and 100
    if (newCurve < 0) newCurve = 0;
    if (newCurve > 100) newCurve = 100;
    curvaturePercentage = newCurve;
    Serial.print("Curvature percentage set to: ");
    Serial.println(curvaturePercentage);
    server.send(200, "text/plain", "Curvature set to " + String(curvaturePercentage));
  } else {
    server.send(400, "text/plain", "Missing 'value' parameter");
  }
});
  server.onNotFound([]() {
    server.send(404, "text/plain", "Endpoint non trovato");
    Serial.println("Richiesta non valida: " + server.uri());
});
}
void setup_pins() {
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

    // Setup PWM channels
  ledcSetup(pwmChannelA, PWM_FREQ, PWM_RES);
  ledcAttachPin(ENA, pwmChannelA);
  ledcSetup(pwmChannelB, PWM_FREQ, PWM_RES);
  ledcAttachPin(ENB, pwmChannelB);
}
void setup() {
  Serial.begin(9600);
  setup_pins();   
  // Connessione al Wi-Fi
  Serial.print("Connessione a ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Connesso! IP: " + WiFi.localIP().toString());

  initialize_HTTP_commands();
  // Avvia il server
  server.begin();
  Serial.println("Firmware version 1.0 – flashed at " + String(__TIME__));
  Serial.println("Server HTTP avviato. In ascolto per comandi...");
}

void loop() {
  server.handleClient(); // Gestisce le richieste HTTP in arrivo
}