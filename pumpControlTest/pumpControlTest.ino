int pin1 = 27;
int pin2 = 19;
void setup() {
  // put your setup code here, to run once:
  pinMode(pin1, OUTPUT);
  pinMode(pin2, OUTPUT);
  //digitalWrite(pin1, HIGH);
  //digitalWrite(pin2, LOW);
  Serial.begin(115200);
  Serial.println("Testing pump control");
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.println("PUMP");
  for(int i = 0; i < 20; i++){
    Serial.println(i);
    if(i%10 == 0){
        Serial.println("LOW");
        digitalWrite(pin1, LOW);
      }
    else if(i == 15){
       Serial.println("HIGH");
        digitalWrite(pin1, HIGH);
      }
  }

}
