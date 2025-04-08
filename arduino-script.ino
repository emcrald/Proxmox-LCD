#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>

hd44780_I2Cexp lcd;

const int LCD_COLS = 16;
const int LCD_ROWS = 2;

String lines[2];
int currentScreen = 0;
unsigned long lastUpdate = 0;
const unsigned long updateInterval = 3000;

void setup() {
  Serial.begin(9600);
  
  int status = lcd.begin(LCD_COLS, LCD_ROWS);
  if(status) {
    hd44780::fatalError(status);
  }

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Waiting for data");
}

void loop() {
  static String incomingLine = "";
  
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      if (incomingLine.length() > 0) {
        int splitIndex = incomingLine.indexOf('|');
        if (splitIndex > -1) {
          lines[0] = incomingLine.substring(0, splitIndex);
          lines[1] = incomingLine.substring(splitIndex + 1);
        }
        incomingLine = "";
      }
    } else {
      incomingLine += c;
    }
  }

  unsigned long now = millis();
  if (now - lastUpdate >= updateInterval) {
    lastUpdate = now;

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(lines[0].substring(0, LCD_COLS));
    lcd.setCursor(0, 1);
    lcd.print(lines[1].substring(0, LCD_COLS));
  }
}
