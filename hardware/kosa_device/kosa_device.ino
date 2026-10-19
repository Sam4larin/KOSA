// KoSa device firmware for Arduino-style boards (Uno, Nano, Mega).
// Speaks one text line each way over USB serial at 9600 baud:
//   PING                       -> PONG
//   D<pin> ON|OFF|LOCK|UNLOCK  -> OK   (ON and LOCK = HIGH, OFF and UNLOCK = LOW), pins 2-13
//   anything else              -> ERR
void setup() {
  Serial.begin(9600);
  Serial.setTimeout(100);        // also accept commands that arrive without a newline
  Serial.println("KoSa ready");  // makes the Wokwi serial monitor appear
}

void loop() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  line.toUpperCase();
  if (line.length() == 0) return;
  if (line == "PING") { Serial.println("PONG"); return; }
  int sp = line.indexOf(' ');
  if (line.charAt(0) == 'D' && sp > 1) {
    int pin = line.substring(1, sp).toInt();
    String cmd = line.substring(sp + 1);
    if (pin >= 2 && pin <= 13 && (cmd == "ON" || cmd == "OFF" || cmd == "LOCK" || cmd == "UNLOCK")) {
      pinMode(pin, OUTPUT);
      digitalWrite(pin, (cmd == "ON" || cmd == "LOCK") ? HIGH : LOW);
      Serial.println("OK");
      return;
    }
  }
  Serial.println("ERR");
}
