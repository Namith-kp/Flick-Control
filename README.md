
# Flick Control

A Gesture Controlled Home Automation using Opencv in Python  that interfaces with an Arduino via a COM port to control LEDs based on hand gestures.



## Demo
![Demo](https://raw.githubusercontent.com/Namith-kp/Flick-Control/main/assets/demo.gif)

## Run Locally

- Clone the project

```bash
  git clone https://github.com/Namith-kp/Flick-Control.git
```

- Go to the project directory

```bash
  cd Flick-Control
```

- Install dependencies

```bash
  pip install opencv-python
  pip install tensorflow
```
- Upload the `arduino/arduino.ino` to the Arduino Board, connect it to the PC to run the project

- Connect LEDs to Arduino board as declared in `arduino/arduino.ino`

- Start the server

```bash
  python3 app.py
```


## Features

- Seamless Single Hand Gestures Detection (can modify to 2 hands)
- Live gestures previews
- Manual Control of LEDs via Buttons
- Can switch to Muiltiple connected cameras


## Screenshots

![App Screenshot 1](https://raw.githubusercontent.com/Namith-kp/Flick-Control/main/assets/HomePage.png)

![App Screenshot 2](https://raw.githubusercontent.com/Namith-kp/Flick-Control/main/assets/MainPage.png)


## 🔗 Links
[![Github](https://img.shields.io/badge/github-1DA1F2?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Namith-kp)
[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/namith-kp)


