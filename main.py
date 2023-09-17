from network_manager import NetworkManager
import uasyncio
from urllib import urequest
import time
import utime
import json
from pimoroni import Button
import jpegdec
import random

from utils.display import Display
from utils.remote import Remote
from utils.process import Process

conf = json.load(open('config.json'))

pico_screen = Display()

WIDTH, HEIGHT = pico_screen.display.get_bounds()

network_manager = NetworkManager(conf['network']['country'])
uasyncio.get_event_loop().run_until_complete(network_manager.client(conf['network']['ssid'], conf['network']['psk']))

button_a = Button(12)
button_b = Button(13)
button_c = Button(14)

def display_info(conf):
    for stage in conf:
        if stage['type'] == "pihole":
            pihole = Remote.get_pihole(stage['address'], stage['auth'])
            if pihole is not None:
                data = Process.display_block_data(pihole)
                pico_screen.write_line(stage['label'], data)
            else:
                pico_screen.write_line(stage['label'], "OFFLINE", 10)
        elif stage['type'] == "synology":
            synnas = Remote.get_synology_nas(stage['address'], stage['user'], stage['auth'])
            if synnas is not None and 'data' in synnas:
                pico_screen.write_line(stage['label'], Process.display_nas_data(synnas['data']['volumes']))
            else:
                pico_screen.write_line(stage['label'], "OFFLINE", 10)
        elif stage['type'] == "prometheus":
            job = stage['user']
            try:
                cpu_aloc = Remote.get_prometheus(stage['address'], "100%20-%20(avg%20by%20(mode)%20(irate(node_cpu_seconds_total%7Bmode%3D%22idle%22%2Cjob%3D%22" + job + "%22%7D%5B5m%5D))%20*%20100)%0A")
                ram_aloc = Remote.get_prometheus(stage['address'], "100%20-%20((node_memory_MemAvailable_bytes%7Bjob%3D%22" + job + "%22%7D%20%2F%20node_memory_MemTotal_bytes%7Bjob%3D%22" + job + "%22%7D)%20*%20100)%0A")
                cpu_temp = Remote.get_prometheus(stage['address'], "avg(node_hwmon_temp_celsius%7Bchip%3D%22platform_coretemp_0%22%2Cjob%3D%22" + job + "%22%2Csensor%3D~%22temp%5B1-5%5D%22%7D)")
            except:
                cpu_aloc = None
                ram_aloc = None
                cpu_temp = None
            if cpu_aloc is not None and cpu_temp is not None and ram_aloc is not None:
                if ('data' in cpu_aloc and 'result' in cpu_aloc['data'] and isinstance(cpu_aloc['data']['result'], list) and len(cpu_aloc['data']['result']) > 0
                and 'data' in cpu_temp and 'result' in cpu_temp['data'] and isinstance(cpu_temp['data']['result'], list) and len(cpu_temp['data']['result']) > 0
                and 'data' in ram_aloc and 'result' in ram_aloc['data'] and isinstance(ram_aloc['data']['result'], list) and len(ram_aloc['data']['result']) > 0):
                    pico_screen.write_line(stage['label'], Process.display_prometheus_details(
                        cpu_aloc['data']['result'],
                        ram_aloc['data']['result'],
                        cpu_temp['data']['result'])
                    )
                else:
                    pico_screen.write_line(stage['label'], "NO DATA", 10)
            else:
                pico_screen.write_line(stage['label'], "OFFLINE", 10)


# set up
pico_screen.quick_text("Ready")
time.sleep(0.5)

print("Ready for input!")

while True:
    if button_a.read():
        pico_screen.inform_loading()
        pico_screen.clear()

        FILENAME = "placekitten.jpg"
        ENDPOINT = "http://placekitten.com/{0}/{1}"

        url = ENDPOINT.format(WIDTH, HEIGHT + random.randint(0, 10))
        print("Requesting URL: {}".format(url))
        socket = urequest.urlopen(url)

        # Load the image data into RAM (if you have enough!)
        data = bytearray(1024 * 10)
        socket.readinto(data)
        socket.close()

        jpeg = jpegdec.JPEG(pico_screen.display)
        jpeg.open_RAM(data)
        jpeg.decode(0, 0)

        pico_screen.display.set_pen(15)
        pico_screen.display.rectangle(0, HEIGHT - 14, WIDTH, 14)

        pico_screen.display.set_pen(0)
        pico_screen.display.text(url, 5, HEIGHT - 9, scale=1)

        pico_screen.commit()

        time.sleep(0.5)
    elif button_b.read():
        pico_screen.inform_loading()
        pico_screen.clear()

        jpeg = jpegdec.JPEG(pico_screen.display)
        jpeg.open_file("fine.jpg")
        jpeg.decode()

        pico_screen.commit()

        time.sleep(0.5)
    elif button_c.read():
        start_time = utime.time() + 350 # Invalidate the first run - cheap trick.

        while True:
            if button_a.is_pressed or button_b.is_pressed:
                    break

            if abs(start_time - utime.time()) > 300:
                pico_screen.inform_loading()
                pico_screen.clear(True)
                display_info(conf['stages'])
                pico_screen.commit()

                start_time = utime.time()

            time.sleep(0.1)
    time.sleep(0.1)
