import board
import neopixel
import os
import time
import json
from concurrent import futures
from argparse import ArgumentParser
from sys import exit

BRIGHTNESS_DEFAULT = 100
ALIVE_COLOR_KEY = "alive"
DEAD_COLOR_KEY = "dead"
UPDATING_COLOR_KEY = "updating"
EMPTY_COLOR_KEY = "empty"
ALIVE_COLOR_DEFAULT = {'r':BRIGHTNESS_DEFAULT, 'g': BRIGHTNESS_DEFAULT, 'b': BRIGHTNESS_DEFAULT}
DEAD_COLOR_DEFAULT = {'r':BRIGHTNESS_DEFAULT, 'g': 0, 'b': 0}
UPDATING_COLOR_DEFAULT = {'r':0, 'g': 0, 'b': BRIGHTNESS_DEFAULT}
EMPTY_COLOR_DEFAULT = {'r':0, 'g': 0, 'b': 0}

def load_statuses(status_file_path):
    try:
        with open(status_file_path) as status_file:
            return json.load(status_file)
    except IOError:
        print("Warning:  Could not open status file to load existing server status flags.")
        return {}

def update_leds(pixels, pixel_count, hosts, status_data, updating_animation, colors):
    for i in range(pixel_count):
        if i >= len(hosts):
            pixels[i] = (colors[EMPTY_COLOR_KEY]["r"], colors[EMPTY_COLOR_KEY]["g"], colors[EMPTY_COLOR_KEY]["b"])
            continue
        if hosts[i] not in status_data:
            pixels[i] = (colors[UPDATING_COLOR_KEY]["r"], colors[UPDATING_COLOR_KEY]["g"], colors[UPDATING_COLOR_KEY]["b"])
            continue
        if updating_animation:
            pixels[i] = (colors[UPDATING_COLOR_KEY]["r"], colors[UPDATING_COLOR_KEY]["g"], colors[UPDATING_COLOR_KEY]["b"])
            time.sleep(0.5)
        if status_data[hosts[i]] == 0:
            pixels[i] = (colors[ALIVE_COLOR_KEY]["r"], colors[ALIVE_COLOR_KEY]["g"], colors[ALIVE_COLOR_KEY]["b"])
        else:
            pixels[i] = (colors[DEAD_COLOR_KEY]["r"], colors[DEAD_COLOR_KEY]["g"], colors[DEAD_COLOR_KEY]["b"])

def save_statuses(status_file_path, status_data):
    with open(status_file_path, "w") as status_file:
        json.dump(status_data, status_file)

def validate_led_config(rootKey, colors):
    if "r" not in colors or "g" not in colors or "b" not in colors:
        exit("Error: " + rootKey + " LED color is missing a color component")
    try:
        validate_led_component(rootKey, colors["r"])
    except ValueError:
        exit("Error: " + rootKey + " Red color value must be an integer between 0 and 255")
    try:
        validate_led_component(rootKey, colors["g"])
    except ValueError:
        exit("Error: " + rootKey + " Green color value must be an integer between 0 and 255")
    try:
        validate_led_component(rootKey, colors["b"])
    except ValueError:
        exit("Error: " + rootKey + " Blue color value must be an integer between 0 and 255")

def validate_led_component(rootKey, component):
    c = int(component)
    if c < 0 or c > 255:
        raise ValueError()

def ping(host, timeout):
    response = os.system("ping -c 1 -w " + timeout + " " + host + " > /dev/null")
    return [host, response]

def ping_hosts(hosts, timeout):
    new_status_data = {}
    with futures.ProcessPoolExecutor(max_workers=8) as pool:
        ping_futures = []
        for i in range(len(hosts)):
            ping_futures.append(pool.submit(ping, hosts[i], timeout))
        while ping_futures:
            done_pings, ping_futures = futures.wait(ping_futures, timeout = 0.5)
            for future in done_pings:
                data = future.result()
                new_status_data[data[0]] = data[1]
    return new_status_data

def load_config_file(path):
    try:
      with open(path) as config_file:
        return json.load(config_file)
    except IOError:
      exit("Error:  Could not open config file " + path)

def clear_pixels(pixel_count):
    pixels = neopixel.NeoPixel(board.D18, pixel_count)
    pixels.fill((0,0,0))

def process_args():
    settings = {}
    argParser = ArgumentParser()
    argParser.add_argument("--clear", action="store", dest="clear")
    argParser.add_argument("-c", "--config", action="store", dest="config")
    argParser.add_argument("-s", "--server", action="append", dest="servers")
    argParser.add_argument("-f", "--file", action="store", dest="status_file")
    argParser.add_argument("-t", "--timeout", action="store", dest="timeout")
    argParser.add_argument("-p", "--pixels", action="store", dest="pixels")
    argParser.add_argument("-a", "--alive", action="store", dest=ALIVE_COLOR_KEY)
    argParser.add_argument("-d", "--dead", action="store", dest=DEAD_COLOR_KEY)
    argParser.add_argument("-u", "--updating", action="store", dest=UPDATING_COLOR_KEY)
    argParser.add_argument("-e", "--empty", action="store", dest=EMPTY_COLOR_KEY)


    args = vars(argParser.parse_args())
    if args["clear"] != None:
        try:
            count = int(args["clear"])
            clear_pixels(count)
            print("Display pixels cleared.")
            exit()
        except ValueError:
            exit("Error:  Clear count must be an integer")

    if args["config"] != None:
        config_data = load_config_file(args["config"])
        if "servers" in config_data:
            settings["servers"] = config_data["servers"]
        if "colors" in config_data:
            settings["colors"] = config_data["colors"]
        if "file" in config_data:
            settings["status_file"] = config_data["file"]
        if "timeout" in config_data:
            settings["timeout"] = config_data["timeout"]
        if "pixels" in config_data:
            settings["pixels"] = config_data["pixels"]

    overlay_arg_settings(args, settings)
    default_settings(settings)
    validate_settings(settings)
    return settings

def overlay_arg_settings(args, settings):
    if args["servers"] != None:
        settings["servers"] = args["servers"]
    if args["status_file"] != None:
        settings["status_file"] = args["status_file"]
    if args["timeout"] != None:
        settings["timeout"] = args["timeout"]
    if args[ALIVE_COLOR_KEY] != None:
        settings["colors"][ALIVE_COLOR_KEY] = load_color_from_string(ALIVE_COLOR_KEY, args[ALIVE_COLOR_KEY])
    if args[DEAD_COLOR_KEY] != None:
        settings["colors"][DEAD_COLOR_KEY] = load_color_from_string(DEAD_COLOR_KEY, args[DEAD_COLOR_KEY])
    if args[UPDATING_COLOR_KEY] != None:
        settings["colors"][UPDATING_COLOR_KEY] = load_color_from_string(UPDATING_COLOR_KEY, args[UPDATING_COLOR_KEY])
    if args[EMPTY_COLOR_KEY] != None:
        settings["colors"][EMPTY_COLOR_KEY] = load_color_from_string(EMPTY_COLOR_KEY, args[EMPTY_COLOR_KEY])

def load_color_from_string(color_key, json_string):
    components = json.loads(json_string)
    component_config = {}
    if "r" in components:
        component_config["r"] = components["r"]
    if "g" in components:
        component_config["g"] = components["g"]
    if "b" in components:
        component_config["b"] = components["b"]
    validate_led_config(color_key, component_config)
    return component_config

def default_settings(settings):
    if "colors" not in settings:
        settings["colors"] = {}
    if "timeout" not in settings:
        settings["timeout"] = "1"
    if ALIVE_COLOR_KEY not in settings["colors"]:
        settings["colors"][ALIVE_COLOR_KEY] = ALIVE_COLOR_DEFAULT
    if DEAD_COLOR_KEY not in settings["colors"]:
        settings["colors"][DEAD_COLOR_KEY] = DEAD_COLOR_DEFAULT
    if UPDATING_COLOR_KEY not in settings["colors"]:
        settings["colors"][UPDATING_COLOR_KEY] = UPDATING_COLOR_DEFAULT
    if EMPTY_COLOR_KEY not in settings["colors"]:
        settings["colors"][EMPTY_COLOR_KEY] = EMPTY_COLOR_DEFAULT

def validate_settings(settings):
    if "servers" not in settings:
        exit("Error:  At least one server must be specified!")
    if "status_file" not in settings:
        exit("Error:  Status file path must be specified!")
    if "pixels" not in settings:
        exit("Error:  Pixel count must be specified!")

    try:
        int(settings["timeout"])
    except ValueError:
        exit("Error:  Timeout must be an integer")

    try:
        int(settings["pixels"])
    except ValueError:
        exit("Error:  Pixels must be an integer")

    validate_led_config(ALIVE_COLOR_KEY, settings["colors"])
    validate_led_config(DEAD_COLOR_KEY, settings["colors"])
    validate_led_config(UPDATING_COLOR_KEY, settings["colors"])
    validate_led_config(EMPTY_COLOR_KEY, settings["colors"])

def main():
    settings = process_args()
    status_file_path = settings["status_file"]
    servers = settings["servers"]
    timeout = settings["timeout"]
    pixel_count = int(settings["pixels"])
    status_data = load_statuses(status_file_path)
    pixels = neopixel.NeoPixel(board.D18, pixel_count)
    update_leds(pixels, pixel_count, servers, status_data, False, settings["colors"])
    updated_status_data = ping_hosts(servers, timeout)
    save_statuses(status_file_path, updated_status_data)
    update_leds(pixels, pixel_count, servers, updated_status_data, True, settings["colors"])

if __name__ == "__main__":
    main()