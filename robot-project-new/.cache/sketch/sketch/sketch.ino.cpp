#include <Arduino.h>
#line 1 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
#include <Arduino_RouterBridge.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <Servo.h>

const int ENA = 3;   
const int IN1 = 4;  
const int IN2 = 7;  

const int ENB = 11;   
const int IN3 = 9; 
const int IN4 = 8;   

int motorSpeed = 255;  
int curvaturePercentage = 100;

const int servoPin = 5;
Servo myServo;

void setServoSpeed(int speed);
void stopServoMotor();

const int LED_R = LED4_R;
const int LED_G = LED4_G;
const int LED_B = LED4_B;

const int trigPin1 = A0;
const int echoPin1 = A0;
const int trigPin2 = A0;
const int echoPin2 = A0;
const int trigPin3 = A0;
const int echoPin3 = A0;
int distance;

Adafruit_MPU6050 mpu;

int FREQUENCY = 500; //500ms

#line 40 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
int get_motor_speed();
#line 44 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
int get_curvature();
#line 48 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void send_IMU_data();
#line 111 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void set_led4_color(bool r, bool g, bool b);
#line 117 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void move_forward();
#line 128 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void move_backward();
#line 139 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void turn_left();
#line 150 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void turn_right();
#line 164 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void turn_left_slowly();
#line 179 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void turn_right_slowly();
#line 194 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void stop_motors();
#line 209 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void bridge_handshake_ack();
#line 214 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void detect_obstacle();
#line 237 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void setup();
#line 284 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
void loop();
#line 40 "/home/arduino/ArduinoApps/Robot-for-Post-Hurricane-Agricultural-Inspection/robot-project-new/sketch/sketch.ino"
int get_motor_speed() {
  return motorSpeed;
}

int get_curvature() {
  return curvaturePercentage;
}

void send_IMU_data(){
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  String data = String(a.acceleration.x) + "," + 
              String(a.acceleration.y) + "," + 
              String(a.acceleration.z) + "," +
              String(g.gyro.x) + "," +
              String(g.gyro.y) + "," +
              String(g.gyro.z);

  Bridge.notify("get_imu",data);
}

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

      duration = pulseIn(echoPin, HIGH, 30000); //<-- if the sonars are not plugged in, this code is blocking
      
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

// supposing the rightmotor is ENA
void turn_left_slowly() {

  int internalWheelSpeed = motorSpeed * (100 - curvaturePercentage) / 100;

  digitalWrite(IN1, HIGH);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, motorSpeed);  
  analogWrite(ENB, internalWheelSpeed);
  set_led4_color(false, false, true);
  Bridge.notify("print_movement","left_slowly");
}

// supposing the rightmotor is ENA
void turn_right_slowly() {

  int internalWheelSpeed = motorSpeed * (100 - curvaturePercentage) / 100;

  digitalWrite(IN1, HIGH);     
  digitalWrite(IN2, LOW);  
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, internalWheelSpeed);
  analogWrite(ENB, motorSpeed);
  set_led4_color(true, true, false);

  Bridge.notify("print_movement","right_slowly");
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

const int obstacleSafeDistance = 20;
void detect_obstacle()
{
  // cm
  const int initData = -1;
  int d1 = sonar1.getDistance();
  int d2 = sonar2.getDistance();
  int d3 = sonar3.getDistance();
  if ( (d1 != initData && d1 < obstacleSafeDistance)
      || (d2 != initData && d2 < obstacleSafeDistance)
      || (d3 != initData && d3 < obstacleSafeDistance))
  {
    Bridge.notify("isObstacle", 1);
  }
  else
  {
    Bridge.notify("isObstacle", 0);
  }
}


int get_sonar_1();
int get_sonar_2();
int get_sonar_3();
void setup() {

  Serial.begin(9600);
  delay(3000);
  Wire.begin();
  mpu.begin();
  
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
  Bridge.provide("turn_left_slowly", turn_left_slowly);
  Bridge.provide("turn_right_slowly", turn_right_slowly);
  Bridge.provide("stop_motors", stop_motors);
  
  Bridge.provide("get_motor_speed", get_motor_speed);
  Bridge.provide("get_curvature", get_curvature);
  
  Bridge.provide("setServoSpeed", setServoSpeed);
  Bridge.provide("stopServoMotor", stopServoMotor);
  delay(500);
  Bridge.notify("handshake_complete", "arduino_ready");
  Bridge.notify("set_speed","");
}

unsigned long lastHandshakeTime = 0;
unsigned long lastIMUtime = 0;
const unsigned long IMU_INTERVAL = 500; // 500 ms

void loop() {
  if (millis() - lastHandshakeTime > 1000) {
    Bridge.notify("handshake_complete", "arduino_ready");
    lastHandshakeTime = millis();
  }
  
  if (millis() - lastIMUtime >= IMU_INTERVAL) {
    lastIMUtime = millis();
    send_IMU_data();
  }
}

void setServoSpeed(int speed){
  Serial.print("BAU");
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

