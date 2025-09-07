import serial
import time

# Set up the serial connection (adjust COM port and baud rate)
comport = 'COM3'  # Replace with your COM port
baud_rate = 9600

arduino = serial.Serial(comport, baud_rate, timeout=1)
time.sleep(2)  # Give the connection a moment to initialize

def led(fingers_up, type):
    if type == 1:
        # Send the states of all LEDs at once
        command = ''.join(map(str, fingers_up))  # Create a string like '10101'
        arduino.write(f"SET:{command}\n".encode())
    elif type == 2:
        # Count the number of "fingers_up"
        count = sum(fingers_up)
        arduino.write(f"COUNT:{count}\n".encode())
    else:
        print("Invalid type. Use 1 for direct control or 2 for counting mode.")

# # Example usage:
# fingers_up_example = [1, 0, 1, 0, 1]  # Example input
# led(fingers_up_example, 1)  # Direct control mode
# time.sleep(1)
# led(fingers_up_example, 2)  # Counting mode
# time.sleep(1)

# Close the connection when done
# arduino.close()
