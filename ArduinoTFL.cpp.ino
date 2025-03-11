#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>

// Include the correct font
#include "LondonUnderground12pt7b.h"

// LCD pins
#define TFT_CS 10
#define TFT_RST 9
#define TFT_DC 8

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);

String incomingData = "";

void setup() {
  Serial.begin(9600);
  tft.begin();
  tft.setRotation(3);
  tft.setFont(&LondonUndergroundRegular8pt7b);
  tft.fillScreen(ILI9341_BLACK);
  tft.setTextColor(ILI9341_WHITE);
  tft.setTextSize(1);
  tft.setCursor(10, 18);
  tft.println("Waiting for data...");
}

void loop() {
  // Read full message until newline
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      displayData(incomingData);
      incomingData = "";
    } else {
      incomingData += c;
    }
  }
}

void displayData(String data) {
  // Clear screen once
  tft.fillScreen(ILI9341_BLACK);
  tft.setTextColor(ILI9341_YELLOW);
  tft.setFont(&LondonUndergroundRegular8pt7b);
  tft.setTextSize(1);

  int yPosition = 18;

  // Split the message using '|'
  int startIndex = 0;
  int delimiterIndex = data.indexOf('|');

  while (delimiterIndex != -1) {
    String line = data.substring(startIndex, delimiterIndex);

    // Find space between station and time
    int separatorIndex = line.lastIndexOf(',');
    
    if (separatorIndex != -1) {
      String station = line.substring(0, separatorIndex);
      String timeStr = line.substring(separatorIndex + 1);

      // Calculate width dynamically for right alignment
      int timeWidth = timeStr.length() * 10; // Adjust based on font
      int xPosition = 320 - timeWidth - 8; // Right-align with 10px margin

      // Print station name on the left
      tft.setCursor(10, yPosition);
      tft.print(station);
      
      // Print time aligned to the right
      tft.setCursor(xPosition, yPosition);
      tft.print(timeStr);
    }

    yPosition += 25;
    startIndex = delimiterIndex + 1;
    delimiterIndex = data.indexOf('|', startIndex);

    // Prevent text overflow
    if (yPosition > 300) break;
  }
}
