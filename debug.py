def debug_wifi_connection(esp, socket):
    print("Testing wifi connection")

    print("My IP address is", esp.pretty_ip(esp.ip_address))
    print(
        "IP lookup adafruit.com: %s" % esp.pretty_ip(esp.get_host_by_name("adafruit.com"))
    )
    print("Ping google.com: %d ms" % esp.ping("google.com"))

    print("ESP32 SPI webclient test")
    import adafruit_requests as requests

    TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
    JSON_URL = "http://api.coindesk.com/v1/bpi/currentprice/USD.json"

    requests.set_socket(socket, esp)

    esp._debug = True
    print("Fetching text from", TEXT_URL)
    r = requests.get(TEXT_URL)
    print("-" * 40)
    print(r.text)
    print("-" * 40)
    r.close()

    print()
    print("Fetching json from", JSON_URL)
    r = requests.get(JSON_URL)
    print("-" * 40)
    print(r.json())
    print("-" * 40)
    r.close()
    print("Wifi Test Done!")

def debug_esp32spi(esp):
    from adafruit_esp32spi import adafruit_esp32spi
    print("ESP32 SPI hardware test")

    if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
        print("ESP32 found and in idle mode")
    print("Firmware vers.", esp.firmware_version)
    print("MAC addr:", [hex(i) for i in esp.MAC_address])
    print("MAC addr:", ':'.join([hex(i) for i in esp.MAC_address]))

    for ap in esp.scan_networks():
        print("\t%s\t\tRSSI: %d" % (str(ap['ssid'], 'utf-8'), ap['rssi']))

    print("Done!")

def debug_pm25(aqdata):
    print("PM25 DEBUG OUTPUT")
    print(aqdata)
    print()
    print("Concentration Units (standard)")
    print("-----------------------------------")
    print(
        "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
        % (
            aqdata["pm10 standard"],
            aqdata["pm25 standard"],
            aqdata["pm100 standard"]
        )
    )

    print("Concentration Units (environmental)")
    print("-----------------------------------")
    print(
        "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
        % (
            aqdata["pm10 env"],
            aqdata["pm25 env"],
            aqdata["pm100 env"]
        )
    )
    print("Particles > 0.3um / 0.1L air:", aqdata["particles 03um"])
    print("Particles > 0.5um / 0.1L air:", aqdata["particles 05um"])
    print("Particles > 1.0um / 0.1L air:", aqdata["particles 10um"])
    print("Particles > 2.5um / 0.1L air:", aqdata["particles 25um"])
    print("Particles > 5.0um / 0.1L air:", aqdata["particles 50um"])
    print("Particles > 10 um / 0.1L air:", aqdata["particles 100um"])
    print("-----------------------------------")

def debug_aht(aht):
    print()
    print("Testing AHT20")
    print("Temperature: %0.1f C" % aht.temperature)
    print("Humidity: %0.1f %%" % aht.relative_humidity)
