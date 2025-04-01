from sciencemode import sciencemode
import time
import numpy as np
from scipy.signal import butter, filtfilt

###### Digital Filter #########

# Butterworth filter design function: designs a low-pass Butterworth filter
def butter_lowpass(cutoff, fs, order=5):
    nyquist = 0.5 * fs  # Nyquist frequency half the sampling rate
    normal_cutoff = cutoff / nyquist  # Normalized cutoff frequency
    b, a = butter(order, normal_cutoff, btype='low', analog=False)  
    return b, a

# Function to apply the low-pass Butterworth filter to data
def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)  
    y = filtfilt(b, a, data)  # Apply the filter to the data using forward and backward passes
    return y

# Filter Parameters
cutoff = 60  # Cutoff frequency for the filter in Hz
fs = 4000  # Sampling rate in Hz
order = 10  # Order of the filter (higher order : sharper cutoff)

# storing the pulse values during stimulation
pulse_values = []

# PID controller class to adjust the current based on feedback control
class PID:
    def __init__(self, Kp, Ki, Kd, setpoint):
        self.Kp = Kp  # Proportional gain
        self.Ki = Ki  # Integral gain
        self.Kd = Kd  # Derivative gain
        self.setpoint = setpoint  # Desired setpoint
        self.integral = 0  # Integral accumulator
        self.previous_error = 0  # previous error to compute derivative

    # Function to compute the control output based on PID control 
    def compute(self, measurement, dt):
        error = self.setpoint - measurement  # Error between setpoint and measurement
        self.integral += error * dt  # Update integral with the accumulated error
        derivative = (error - self.previous_error) / dt  # Derivative of error
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative  # PID formula
        self.previous_error = error  # Store current error for next iteration
        return output  

# PID parameters (tuned based on current parameter settings / can be changed)
Kp = 1.0  
Ki = 0.1 
Kd = 0.05  
setpoint = 2.0  # Desired current level in mA

pid = PID(Kp, Ki, Kd, setpoint)

# Initialize communication with the device
ack = sciencemode.ffi.new("Smpt_ack*")  # Allocate memory for acknowledgment
device = sciencemode.ffi.new("Smpt_device*")  # Allocate memory for the device
extended_version_ack = sciencemode.ffi.new("Smpt_get_extended_version_ack*")  # Memory for device info

com = sciencemode.ffi.new("char[]", b"COM5")  # Specify the serial port for communication (COM7)

# Check if the serial port is available
ret = sciencemode.smpt_check_serial_port(com)
print(f"Port check is {ret}")  # Output the result of the port check

# Open the serial port for communication with the device
ret = sciencemode.smpt_open_serial_port(device, com)
print(f"smpt_open_serial_port: {ret}")  # Output the result of opening the port

# Generate the next packet number for communication (ensures synchronization with device)
packet_number = sciencemode.smpt_packet_number_generator_next(device)
print(f"next packet_number {packet_number}")  # Output the next packet number

# Send a request to get extended version information from the device
ret = sciencemode.smpt_send_get_extended_version(device, packet_number)
print(f"smpt_send_get_extended_version: {ret}")  # Output the result of sending the request

# Wait for a response packet from the device
while not sciencemode.smpt_new_packet_received(device):
    time.sleep(1)  

# Get the last acknowledgment packet from the device
sciencemode.smpt_last_ack(device, ack)
print(f"command number {ack.command_number}, packet_number {ack.packet_number}")  # Output command info

# Retrieve the extended version information from the device
ret = sciencemode.smpt_get_get_extended_version_ack(device, extended_version_ack)
print(f"smpt_get_get_extended_version_ack: {ret}") 
print(f"fw_hash {extended_version_ack.fw_hash}")  # Output the firmware hash

# Initialize the stimulation protocol 
ml_init = sciencemode.ffi.new("Smpt_ml_init*")
ml_init.packet_number = sciencemode.smpt_packet_number_generator_next(device)  # Generate next packet number
ret = sciencemode.smpt_send_ml_init(device, ml_init)  # Send the initialization command to the device
print(f"smpt_send_ml_init: {ret}") 
time.sleep(1)  # Pause for 1 second to ensure the device is ready

# Prepare the update packet for stimulation (ml_update)
ml_update = sciencemode.ffi.new("Smpt_ml_update*")
ml_update.packet_number = sciencemode.smpt_packet_number_generator_next(device)  # Generate next packet number
channel = 1 # Specify which channel to use for stimulation
point_time = 700  # Time duration for each phase of the pulse in microseconds
point_current = 5  # Initial current level in mA
point_period = point_time * 10  # Total period of the biphasic pulse (1/frequency)
# Configure the stimulation pulse on the specified channel
ml_update.enable_channel[channel] = True  # Enable stimulation on the channel
ml_update.channel_config[channel].period = point_period  # Set total pulse period
ml_update.channel_config[channel].number_of_points = 2  # Two points: positive and negative phases

# Configure the positive phase of the pulse
ml_update.channel_config[channel].points[0].time = point_time  # Duration of positive pulse
ml_update.channel_config[channel].points[0].current = point_current  # Current for positive pulse

# Configure the negative phase of the pulse
ml_update.channel_config[channel].points[1].time = point_time  # Duration of negative pulse
ml_update.channel_config[channel].points[1].current = -point_current  # Current for negative pulse

# # Configure the negative phase of the pulse
# ml_update.channel_config[channel].points[2].time = 10000  # Duration of negative pulse
# ml_update.channel_config[channel].points[2].current = 0  # Current for negative pulse

# Ask the user to choose between continuous or timed stimulation
choice = input("Enter '1' for continuous pulse or '2' for timed stimulation: ")



# Main loop: execute stimulation 
try:
    if choice == "1":
        # Continuous biphasic pulse stimulation
        previous_time = time.time()  # Record the starting time
        while True:
            current_time = time.time()  # Get current time
            dt = current_time - previous_time  # Calculate time difference (delta time)
            
            ml_update.packet_number = sciencemode.smpt_packet_number_generator_next(device)  # Get next packet number
            ret = sciencemode.smpt_send_ml_update(device, ml_update)  # Send stimulation update to device
            print(f"smpt_send_ml_update: {ret}")  # Output the result
            
            current_pulse_value = ml_update.packet_number  # Use packet number as pulse value
            pulse_values.append(current_pulse_value)  # Store pulse value for filtering
            
            # If enough pulse values are collected, apply the low-pass filter
            if len(pulse_values) > fs:  # Ensure we have enough data points
                smoothed_pulse_values = butter_lowpass_filter(pulse_values, cutoff, fs, order)  # Filter data
                smoothed_pulse_value = smoothed_pulse_values[-1]  # Get the latest smoothed value
                
                # Use PID controller to compute the control signal (adjust the current)
                control_signal = pid.compute(smoothed_pulse_value, dt)
                point_current = max(min(control_signal, 10), -10)  # Limit current between -10 and 10 mA
                
                # Update the pulse configuration with the adjusted current
                ml_update.channel_config[channel].points[0].current = point_current  # Positive phase
                ml_update.channel_config[channel].points[1].current = -point_current  # Negative phase
                ml_update.channel_config[channel].points[2].current = 0  
                print(f"Smoothed Pulse Value: {smoothed_pulse_value}, Control Signal: {control_signal}, Adjusted Current: {point_current}")
            
            previous_time = current_time  # Update the previous time for next iteration
            time.sleep(0.02)  # Sleep for 20ms to match the stimulation period

    elif choice == "2":
        # Timed stimulation: stimulate for a user-defined duration
        duration_ms = int(input("How long do you want to stimulate (in milliseconds)? "))  # Ask user for duration
        start_time = time.time()  # Record the start
        previous_time = start_time
        while (time.time() - start_time) * 1000 < duration_ms: # execute for input duration in ms (by changing multiplied number(here : 1000), user can adjust duration in micro-second or second etc)
            current_time = time.time()
            dt = current_time - previous_time
            
            ml_update.packet_number = sciencemode.smpt_packet_number_generator_next(device)
            ret = sciencemode.smpt_send_ml_update(device, ml_update)
            print(f"smpt_send_ml_update: {ret}")
            
            current_pulse_value = ml_update.packet_number
            pulse_values.append(current_pulse_value)
            
            # Apply the Butterworth filter to the pulse values
            if len(pulse_values) > fs:  # Ensure enough data points
                smoothed_pulse_values = butter_lowpass_filter(pulse_values, cutoff, fs, order)
                smoothed_pulse_value = smoothed_pulse_values[-1]
                
                # Apply PID control
                control_signal = pid.compute(smoothed_pulse_value, dt)
                point_current = max(min(control_signal, 10), -10)  # Limit current to a range of -10 to 10 mA
                
                # Update pulse configuration with new current
                ml_update.channel_config[channel].points[0].current = point_current
                ml_update.channel_config[channel].points[1].current = -point_current
                ml_update.channel_config[channel].points[2].current = 0 
                print(f"Smoothed Pulse Value: {smoothed_pulse_value}, Control Signal: {control_signal}, Adjusted Current: {point_current}")
            
            previous_time = current_time
            time.sleep(0.02)  
            
    else:
        print("Invalid choice. Please enter '1' or '2'.")

except KeyboardInterrupt:   # stopping stimulation by keyboard interrupt
    print("Stopping stimulation")

# Stop the stimulation
packet_number = sciencemode.smpt_packet_number_generator_next(device)
ret = sciencemode.smpt_send_ml_stop(device, packet_number)
print(f"smpt_send_ml_stop: {ret}")  # stimulation stopped
frq=1/(point_period*1e-6)
print(f"pulse width : {point_period}")     # print frequency when stopped
ret = sciencemode.smpt_close_serial_port(device)  
print(f"smpt_close_serial_port: {ret}")
