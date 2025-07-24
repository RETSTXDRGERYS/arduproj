#include <Servo.h>
#include <avr/wdt.h>  // For watchdog reset

Servo esc;
int potPin = A0;
const int buttonPin = 2;
const int ledPin = 13;  // Built-in LED
const int buzzerPin = 11;

int currentSpeed = 1000;  // Start at minimum
int targetSpeed;
bool isArmed = false;
bool lastButtonState = HIGH;

void setup() {
    esc.attach(9);  // ESC signal wire
    Serial.begin(9600);

    pinMode(buttonPin, INPUT_PULLUP);  // Button wired to GND
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, LOW);
    pinMode(buzzerPin, OUTPUT);

    Serial.println("Waiting for arming button...");

    // Wait for button press
    while (digitalRead(buttonPin) == HIGH) {
        delay(10);
    }

    Serial.println("Button pressed. Arming...");

    // Blink LED while arming
    for (int i = 0; i < 4; i++) {
        digitalWrite(ledPin, HIGH);
        delay(150);
        digitalWrite(ledPin, LOW);
        delay(150);
        tone(buzzerPin, 1000);
        delay(1000);
        noTone(buzzerPin);

    }

    // Step 1: Neutral throttle
    esc.writeMicroseconds(1500);
    Serial.println("Neutral...");
    delay(1000);

    // Step 2: Full reverse (brake)
    esc.writeMicroseconds(1000);
    Serial.println("Reverse to arm...");
    delay(1500);

    // Step 3: Back to neutral
    esc.writeMicroseconds(1000);
    Serial.println("Armed. Back to neutral.");
    delay(500);

    digitalWrite(ledPin, HIGH);  // LED solid ON when armed
    isArmed = true;
}

void loop() {
    if (!isArmed) return;

    // Check for reset button press
    bool currentButtonState = digitalRead(buttonPin);
    if (currentButtonState == LOW && lastButtonState == HIGH) {
        Serial.println("Button pressed again   flashing LED and resetting...");

        // Flash LED before reset
        for (int i = 0; i < 5; i++) {
            digitalWrite(ledPin, LOW);
            tone(buzzerPin, 1000);
            delay(100);
            noTone(buzzerPin);
            digitalWrite(ledPin, HIGH);
            tone(buzzerPin, 1000);
            delay(100);
            noTone(buzzerPin);
        }

        // Reset using watchdog
        wdt_enable(WDTO_15MS);  // Enable short timeout
        while (true);           // Wait for reset
    }
    lastButtonState = currentButtonState;

    int potValue = analogRead(potPin);
    Serial.print("Pot Value: ");
    Serial.print(potValue);
    Serial.print(" | ");

    targetSpeed = map(potValue, 0, 1023, 1000, 2000);
    Serial.print("Target: ");
    Serial.print(targetSpeed);
    Serial.print(" | ");

    esc.writeMicroseconds(targetSpeed);
    Serial.print("Current: ");
    Serial.println(targetSpeed);
    delay(10);
}

