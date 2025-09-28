import network
import socket
import time
from machine import Pin, PWM

# LED pins
led_external = Pin(16, Pin.OUT)  # Renamed for clarity
led_onboard = Pin("LED", Pin.OUT)

# --- Setup PWM for ESC ---
pwm = PWM(Pin(15))
pwm.freq(50)
current_micros = 1000

def set_esc(micros):
    global current_micros
    micros = max(1000, min(2000, micros)) # Clamp to safe range
    duty = int((micros / 20000.0) * 65535)
    pwm.duty_u16(duty)
    current_micros = micros
    # print(f"ESC set to: {micros}us, Duty: {duty}") # Optional: for debugging
    return micros, duty

def ramp_to(target_micros, step=10, delay_ms=20): # Adjusted step and delay
    """Gradually move from current_micros to target_micros."""
    global current_micros
    # print(f"Ramping from {current_micros}us to {target_micros}us")
    if target_micros == current_micros:
        return

    actual_step = step if target_micros > current_micros else -step
    
    for us in range(current_micros + actual_step, target_micros + actual_step, actual_step):
        set_esc(us)
        time.sleep_ms(delay_ms)
    
    # Ensure final target is set if range doesn't exactly hit it
    if current_micros != target_micros:
        set_esc(target_micros)
    # print(f"Ramping complete. Current: {current_micros}us")


def set_esc_percent(percent):
    percent = max(0, min(100, percent))
    target_micros = 1000 + int((percent / 100.0) * 1000)
    ramp_to(target_micros)
    return current_micros, pwm.duty_u16() # Return current state after ramp

led_onboard.on() # Signal script start

# --- ESC Startup Arming Sequence ---
print("Arming ESC...")
set_esc(1500) # Neutral
print("Neutral (1500us)")
time.sleep(1)

set_esc(1000) # Min throttle
print("Min Throttle for arming (1000us)")
time.sleep(1.5)

# Assuming armed and ready at min throttle
print("Armed. Standing by at min throttle (1000us).")
time.sleep(0.5)
# -----------------------------------

# --- WiFi Setup ---
SSID = "pico" # Your SSID
PASSWORD = "gbg64rra" # Your Password

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    print(f"Connecting to WiFi (SSID: {SSID})...")
    wlan.connect(SSID, PASSWORD)
    max_wait = 20
    while max_wait > 0 and not wlan.isconnected():
        print(".")
        time.sleep(1)
        max_wait -= 1

if wlan.isconnected():
    ip_address = wlan.ifconfig()[0]
    print(f"Wi-Fi Connected! IP Address: {ip_address}")
    led_onboard.off() # Signal WiFi connected
else:
    print("Wi-Fi Connection Failed!")
    while True: # Blink error
        led_onboard.toggle()
        time.sleep(0.2)
    # Machine will likely halt here or reboot if error handling isn't more robust

# --- Web Server ---
time.sleep(1) # Short delay before starting server
led_onboard.on() # Signal server start
try:
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow address reuse
    s.bind(addr)
    s.listen(1) # Listen for 1 incoming connection at a time
    print("Listening on", addr)
    led_onboard.off() # Signal server ready
except OSError as e:
    print(f"Error setting up server socket: {e}")
    print("Pico will restart in 5 seconds...")
    time.sleep(5)
    import machine
    machine.reset() # Restart if socket setup fails (e.g. address in use)


def blink_external_led(times=3, delay_sec=0.2): # Changed name for clarity
    for _ in range(times):
        led_external.on()
        time.sleep(delay_sec)
        led_external.off()
        time.sleep(delay_sec)

while True:
    cl = None # Initialize cl
    try:
        cl, client_addr = s.accept()
        cl.settimeout(3.0) # Set a timeout for client operations
        print(f"\nClient connected from: {client_addr}")

        # Read the request line
        request_line_bytes = cl.readline()
        if not request_line_bytes or request_line_bytes == b"\r\n":
            print("Empty or keep-alive request.")
            cl.close()
            continue

        request_line = request_line_bytes.decode('utf-8', 'ignore').strip()
        print(f"Request Line: {request_line}")

        # Read and ignore headers (basic implementation)
        while True:
            header_line = cl.readline()
            if not header_line or header_line == b"\r\n":
                break
            # print(f"Header: {header_line.decode('utf-8', 'ignore').strip()}")


        # Parse the request line (basic)
        parts = request_line.split()
        if len(parts) < 2:
            response_status = "400 Bad Request"
            response_body_str = "Malformed Request Line"
        else:
            method = parts[0]
            full_path = parts[1]
            path = full_path.split('?', 1)[0]

            print(f"Method: {method}, Path: {path}")

            response_status = "200 OK"
            response_body_str = "PICO: Hello!" # Default

            if method == "GET":
                if path == "/led_on":
                    led_external.on()
                    response_body_str = "PICO: External LED ON"
                elif path == "/led_off":
                    led_external.off()
                    response_body_str = "PICO: External LED OFF"
                elif path == "/blink":
                    blink_external_led()
                    response_body_str = "PICO: External LED blinked"
                elif path == "/status":
                    response_body_str = "PICO LED is " + ("ON" if led_external.value() else "OFF")
                    response_body_str += f", Current ESC pulse: {current_micros}us"
                elif path == "/throttle":
                    query_string = ""
                    if '?' in full_path:
                        query_string = full_path.split('?', 1)[1]
                    
                    params = {}
                    if query_string:
                        param_pairs = query_string.split('&')
                        for pair in param_pairs:
                            if '=' in pair:
                                key_val = pair.split('=', 1)
                                if len(key_val) == 2:
                                    params[key_val[0]] = key_val[1]
                    
                    if 'val' in params:
                        try:
                            value = int(params['val'])
                            micros, _ = set_esc_percent(value) # This now ramps
                            response_body_str = f"PICO: Throttle set to {value}% ({micros}us)"
                        except ValueError:
                            response_status = "400 Bad Request"
                            response_body_str = "PICO ERROR: Invalid throttle value format"
                        except Exception as e:
                            response_status = "500 Internal Server Error"
                            response_body_str = f"PICO ERROR: Throttle processing error: {e}"
                    else:
                        response_status = "400 Bad Request"
                        response_body_str = "PICO ERROR: 'val' parameter missing for throttle"
                else:
                    response_status = "404 Not Found"
                    response_body_str = "PICO ERROR: Path not found"
            else:
                response_status = "405 Method Not Allowed"
                response_body_str = "PICO ERROR: Method not allowed (GET only)"

        # Prepare and send the response
        response_body_bytes = response_body_str.encode('utf-8')
        
        http_response = f"HTTP/1.1 {response_status}\r\n"
        http_response += "Content-Type: text/plain; charset=utf-8\r\n" # Use text/plain for simple messages
        http_response += f"Content-Length: {len(response_body_bytes)}\r\n"
        http_response += "Connection: close\r\n" # Important: tell client we will close
        http_response += "\r\n" # Blank line separates headers from body
        http_response += response_body_str # Send body as string, already encoded if needed

        print(f"Pico Replying With Status: {response_status}, Body: '{response_body_str}'")
        
        cl.sendall(http_response.encode('utf-8')) # Encode the whole response at once
        print("Pico response sent.")

    except OSError as e:
        print(f"Socket/Network Error: {e}")
        # This can happen if client disconnects early, etc.
    except Exception as e:
        print(f"An error occurred in request loop: {e}")
        # Attempt to send an error response if client is still connected
        if cl:
            try:
                error_body = f"PICO Server Error: {e}".encode('utf-8')
                error_response = "HTTP/1.1 500 Internal Server Error\r\n"
                error_response += "Content-Type: text/plain; charset=utf-8\r\n"
                error_response += f"Content-Length: {len(error_body)}\r\n"
                error_response += "Connection: close\r\n\r\n"
                cl.sendall(error_response.encode('utf-8') + error_body)
            except Exception as e_send:
                print(f"Failed to send error response: {e_send}")
    finally:
        if cl:
            try:
                cl.close()
                # print("Client connection closed.")
            except Exception as e_close:
                print(f"Error closing client socket: {e_close}")
