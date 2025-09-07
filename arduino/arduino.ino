// Pin definitions using GPIO numbers
int ledPins[] = {14, 5, 4, 0, 2}; // GPIO pins corresponding to D1, D2, D3, D4, D5
int numLeds = 5;

void setup() {
  // Set all LED pins as OUTPUT
  for (int i = 0; i < numLeds; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW); // Turn off all LEDs initially
  }
  
  // Initialize serial communication
  Serial.begin(9600);
}

void loop() {
  // Check if data is available on the serial port
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Read until newline
    command.trim(); // Remove any trailing newline or whitespace

    if (command.startsWith("SET:")) {
      // Command to directly set LED states, e.g., "SET:10101"
      String ledStates = command.substring(4); // Extract the LED states
      for (int i = 0; i < numLeds && i < ledStates.length(); i++) {
        if (ledStates[i] == '1') {
          digitalWrite(ledPins[i], HIGH);
        } else {
          digitalWrite(ledPins[i], LOW);
        }
      }
    } else if (command.startsWith("COUNT:")) {
      // Command to light LEDs based on the count, e.g., "COUNT:3"
      int count = command.substring(6).toInt();
      for (int i = 0; i < numLeds; i++) {
        if (i == count - 1) {
          digitalWrite(ledPins[i], HIGH);
        } else {
          digitalWrite(ledPins[i], LOW);
        }
      }
    } else {
      // Unknown command
      Serial.println("ERROR: Unknown command");
    }
  }
}
