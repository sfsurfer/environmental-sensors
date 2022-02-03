import board
import digitalio
import time
import neopixel
import busio
import displayio
import terminalio
import adafruit_displayio_ssd1306
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_display_text import label
from digitalio import DigitalInOut
from adafruit_pm25.i2c import PM25_I2C
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_ahtx0

from debug import *

DEBUG=False

displayio.release_displays()

# NEOPIXEL Test
# pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
# pixel.brightness = 0.1


print("Initializing Display")
WIDTH = 128
HEIGHT = 64
BORDER = 5

#i2c0 = busio.I2C(board.D25, board.D24, frequency=100000)
i2c1 = busio.I2C(board.SCL, board.SDA, frequency=100000)

display_bus = displayio.I2CDisplay(i2c1, device_address=0x3d)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

## Default display test below
# splash = displayio.Group()
# display.show(splash)

# color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
# color_palette = displayio.Palette(1)
# color_palette[0] = 0xFFFFFF  # White

# bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
# splash.append(bg_sprite)

# # Draw a smaller inner rectangle
# inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
# inner_palette = displayio.Palette(1)
# inner_palette[0] = 0x000000  # Black
# inner_sprite = displayio.TileGrid(
#     inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
# )
# splash.append(inner_sprite)

# Draw a label
text = "Initializing"
text_area = label.Label(
    terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=HEIGHT // 2 - 1
)
# splash.append(text_area)
display.show(text_area)

## End display test

print("Initialize Sensors")
reset_pin = None

pm25 = PM25_I2C(i2c1, reset_pin)
aht = adafruit_ahtx0.AHTx0(i2c1)

print("Initializing Wi-Fi")
esp32_cs = DigitalInOut(board.RX)
esp32_ready = DigitalInOut(board.D11)
esp32_reset = DigitalInOut(board.D12)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

if DEBUG:
    debug_esp32spi(esp)

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)

if DEBUG:
    debug_wifi_connection(esp, socket)

print("Initializing MQTT Client")
pm25_topic = "sensors/pm25"
aht_topic = "sensors/temp_humidity"

MQTT.set_socket(socket, esp)
mqtt_client = MQTT.MQTT(
    broker=secrets["broker"], port=1883
)

def underscore_spaces(s):
    res = ""
    for c in s:
        res += ("_" if c == " " else c)
    return res

try:
    print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
    print("Attempting to connect to mqtt broker")
    mqtt_client.connect()

    print("Found PM2.5 sensor, starting data read loop...")
    while True:
        while not esp.is_connected:
            print("WiFi Not connected, retrying connection")
            try:
                esp.connect_AP(secrets["ssid"], secrets["password"])
            except RuntimeError as e:
                print("could not connect to AP, retrying: ", e)
                continue

        time.sleep(1)

        try:
            aqdata = pm25.read()
        except RuntimeError:
            print("Unable to read from air quality sensor, retrying...")
            continue

        if DEBUG:
            debug_pm25(aqdata)
            debug_aht(aht)

        # Publish Air Quality, Temp and Humidity
        pm25_message = "air_quality " + ",".join(["%s=%f" % (underscore_spaces(k),v) for k,v in aqdata.items()])

        try:
            mqtt_client.publish(pm25_topic, pm25_message)
        except Exception:
            print("ERROR: Failed to publish air quality, retrying")
            try:
                mqtt_client.connect()
                mqtt_client.publish(pm25_topic, pm25_message)
            except Exception as e:
                print("Exception publishing air quality: %s" % e)
                print("ERROR: Failed to publish air quality, continuing")

        try:
            temp = aht.temperature
            humidity = aht.relative_humidity
        except RuntimeError:
            print("Unable to read from temp/humidity sensor, retrying")
            continue

        aht_message = "air_quality temperature=%0.1f,humidity=%0.1f" % (temp, humidity)

        try:
            mqtt_client.publish(aht_topic, aht_message)
        except Exception:
            print("ERROR: Failed to publish mqtt temp & humidity, retrying")
            try:
                mqtt_client.connect()
                mqtt_client.publish(aht_topic, aht_message)
            except Exception as e:
                print("ERROR: Failed to publish mqtt temp & humidity message: %s" % e)

        display_message = '\n'.join([
            "Temperature: %0.1f C" % temp,
            "Humidity: %0.1f%%" % humidity,
#             "PPM 1.0: %0.1f" % aqdata["pm10 standard"],
            "PPM 2.5: %0.1f" % aqdata["pm25 standard"],
            "PPM 10:  %0.1f" % aqdata["pm100 standard"]
        ])

        text_area = label.Label(
            terminalio.FONT, text=display_message, color=0xFFFFFF, x=2, y=5, scale=1
        )
        display.show(text_area)

except Exception as e:
    print("Caught exception: %s" % e)
finally:
    print("Shutting down")
    print("Disconnecting from mqtt broker...")
    mqtt_client.disconnect()
    print("Good bye")
