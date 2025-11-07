// Robust ESP8266 serial relay controller
// Commands (first two characters after trimming):
// "00" -> Relay 0 OFF
// "01" -> Relay 0 ON
// "10" -> Relay 1 OFF
// "11" -> Relay 1 ON

#define RELAY0 D1   // change if needed
#define RELAY1 D2

// If your relay module is active LOW set to true, else false
#define RELAY_ACTIVE_LOW false

void setup() {
  Serial.begin(9600);
  pinMode(RELAY0, OUTPUT);
  pinMode(RELAY1, OUTPUT);

  // Initialize relays OFF (takes into account active low)
  setRelay(RELAY0, false);
  setRelay(RELAY1, false);

  Serial.println();
  Serial.println("ESP8266 Relay Controller Ready");
  Serial.println("Send: 00=R0 OFF, 01=R0 ON, 10=R1 OFF, 11=R1 ON");
  Serial.println("Note: code trims newlines/carriage returns.");
}

void loop() {
  // Wait until a line is available or timeout
  if (Serial.available() > 0) {
    // Read the incoming line (stops at '\n')
    String line = Serial.readStringUntil('\n'); // includes everything up to newline (excludes '\n')
    // There might still be a trailing '\r' if serial monitor sends CRLF — trim removes it
    line.trim(); // removes leading/trailing whitespace including \r and spaces

    // Debugging: show what we actually received (visible and hex)
    Serial.print("RAW received: '");
    Serial.print(line);
    Serial.println("'");

    Serial.print("HEX bytes: ");
    for (size_t i = 0; i < line.length(); ++i) {
      Serial.print("0x");
      if ((uint8_t)line[i] < 0x10) Serial.print('0');
      Serial.print(String((uint8_t)line[i], HEX));
      Serial.print(' ');
    }
    Serial.println();

    // Remove any spaces inside (so "0 1" becomes "01")
    String compact = "";
    for (size_t i = 0; i < line.length(); ++i) {
      if (line[i] == '0' || line[i] == '1') compact += line[i];
    }

    if (compact.length() >= 2) {
      char a = compact.charAt(0);
      char b = compact.charAt(1);
      handleCommand(a, b);
    } else {
      Serial.println("Invalid command (need two digits 0/1). Example: 01");
    }

    // small delay to let serial prints flush
    delay(10);
  }
}

// process the two-digit command
void handleCommand(char c1, char c2) {
  if (c1 == '0' && c2 == '0') {
    setRelay(RELAY0, false);
    Serial.println("Relay 0 OFF");
  }
  else if (c1 == '0' && c2 == '1') {
    setRelay(RELAY0, true);
    Serial.println("Relay 0 ON");
  }
  else if (c1 == '1' && c2 == '0') {
    setRelay(RELAY1, false);
    Serial.println("Relay 1 OFF");
  }
  else if (c1 == '1' && c2 == '1') {
    setRelay(RELAY1, true);
    Serial.println("Relay 1 ON");
  }
  else {
    Serial.println("Invalid command digits. Use only 0 and 1.");
  }
}

// set relay pin considering active low/high module
void setRelay(uint8_t pin, bool on) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(pin, on ? LOW : HIGH);
  } else {
    digitalWrite(pin, on ? HIGH : LOW);
  }
}