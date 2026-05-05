#include <Arduino_RouterBridge.h>
#include <Servo.h>

const int ENA = 3;   
const int IN1 = 4;  
const int IN2 = 2;  

const int ENB = 6;   
const int IN3 = 13; 
const int IN4 = 7;   

int motorSpeed = 255;  

const int servoPin = 5;
Servo myServo;

void setServoSpeed(int speed);
void stopServoMotor();

const int LED_R = LED4_R;
const int LED_G = LED4_G;
const int LED_B = LED4_B;

const int trigPin1 = 9;
const int echoPin1 = 10;
const int trigPin2 = 11;
const int echoPin2 = 12;
const int trigPin3 = 8;
const int echoPin3 = 13;
int distance;      
class Sonar {
  private:

    int trigPin;
    int echoPin;
    int Pos;
    int intervalTimeBetweenUpdates;

  public:
    Sonar() {
        trigPin = 0;
        echoPin = 0;
        Pos = 0;
    }
    Sonar (int trig_pin, int echo_pin, int pos){
      trigPin = trig_pin;
      echoPin = echo_pin;
      Pos = pos;

      pinMode(trigPin, OUTPUT);
      pinMode(echoPin, INPUT);
    }
    int getPos(){
      return Pos;
    }

    int getDistance (){
      long duration;
      int distance;
    
      digitalWrite(trigPin, LOW);
      delayMicroseconds(2);
      digitalWrite(trigPin, HIGH);
      delayMicroseconds(10);
      digitalWrite(trigPin, LOW);
  
      duration = pulseIn(echoPin, HIGH, 30000);

      if (duration == 0) {

        return -1;

      }
      
      distance = duration * 0.0343 / 2;
      
      return distance;
    }
};
Sonar sonar1;
Sonar sonar2;
Sonar sonar3;
void setupSonars();

void set_led4_color(bool r, bool g, bool b) {
  digitalWrite(LED4_R, r ? LOW : HIGH);
  digitalWrite(LED4_G, g ? LOW : HIGH);
  digitalWrite(LED4_B, b ? LOW : HIGH);
}

void move_forward() {
  digitalWrite(IN1, HIGH);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
  set_led4_color(true, false, false);
  Bridge.notify("print_movement", "forward");
}

void move_backward() {
  digitalWrite(IN1, LOW);     
  digitalWrite(IN2, HIGH);  
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
  set_led4_color(false, true, false);
  Bridge.notify("print_movement","backward");
}

void turn_left() {
  digitalWrite(IN1, LOW);     
  digitalWrite(IN2, HIGH);  
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
  set_led4_color(false, false, true);
  Bridge.notify("print_movement","left");
}

void turn_right() {

  digitalWrite(IN1, HIGH);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
  set_led4_color(true, true, false);

  Bridge.notify("print_movement","right");
}

void stop_motors() {

  digitalWrite(IN1, LOW);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  set_led4_color(false, false, false);

  Bridge.notify("print_movement", "stopped");
}

bool bridge_ready = false;

void bridge_handshake_ack() {
  bridge_ready = true;
}

int get_sonar_1();
int get_sonar_2();
int get_sonar_3();
void setup() {

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  myServo.attach(servoPin);

  pinMode(LED4_R, OUTPUT);
  pinMode(LED4_G, OUTPUT);
  pinMode(LED4_B, OUTPUT);

  setupSonars();

  Bridge.begin();
  stop_motors();

  
Bridge.provide("move_forward", move_forward);
Bridge.provide("move_backward", move_backward);
Bridge.provide("turn_left", turn_left);
Bridge.provide("turn_right", turn_right);
Bridge.provide("stop_motors", stop_motors);

Bridge.provide("setServoSpeed", setServoSpeed);
Bridge.provide("stopServoMotor", stopServoMotor);
  
Bridge.notify("handshake_complete", "arduino_ready");

}

void loop() {
  int d1 = -1,d2 = -1,d3 = -1;
  d1 = sonar1.getDistance();
  if (d1!=-1){
    Bridge.notify("sonar_data1",String(d1));
    Serial.println("Ciao");
  }
  d2 = sonar2.getDistance();
  if (d2!=-1){
    Bridge.notify("sonar_data2",String(d2));
    Serial.println("Ciao2");
  }
  d3 = sonar3.getDistance();
  if (d3!=-1){
    Bridge.notify("sonar_data3",String(d3));
    Serial.println("Ciao3");
  }
  delay(10);  

}

void setServoSpeed(int speed){
  myServo.write(speed);
}
void stopServoMotor(){
  myServo.write(90);
}

void setupSonars() {
  sonar1 = Sonar (trigPin1, echoPin1, 1);
  sonar2 = Sonar (trigPin2, echoPin2, 2);
  sonar3 = Sonar (trigPin3, echoPin3, 3);
  Serial.begin(9600);  // Per vedere i valori sul monitor seriale
}
