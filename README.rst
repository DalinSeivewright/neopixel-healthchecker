Neopixel Healthchecker
======================

A python script that will take a list of servers (hostname or ip), will ping through the list (asyncronously, specifically for the reason under gotchas), and then update a pixel colors on a neopixel-like display in the order that the servers were specified.
Each pixel can have one of 4 states:
* Alive:  The ping against the server succeeded.
* Dead:  The ping against the server failed.
* Updating:  The server to be pinged is new to the list and has not been pinged yet, or is in an animation transition stage.
* Empty:  The number of pixels exceeds the number of servers to be pinged.

After the servers are pinged, the statuses are saved to a cache file.  This is because the neopixel library used blanks out the pixels of the display when the display is initialized.  The cache file will load the last ping result of each server to refresh the display.
When the display is refreshed with the new statuses, the script exits.  This is on purpose.  If you need to run this script periodically, I recommend running through a cron job or other scheduler.

Gotchas
-------
* We ping the servers asynchronously simply because of DNS.  When your primary DNS is down, pings will take a considerable amount of time to fallback to the secondary DNS server.  This can be configured of course but I didn't want to deal with DNS configuration on clients so running pings asynchronously helps.


Configuration Options
---------------------
All configuration options can be set via commandline arguments or a config file.  If an option is specified in the configuration file and is also specified via commandline, **the commandline will override the configuration file settings.**

* **-c**, **--config**: Specifies the path to the configuration file.
* **-s**, **--server**: Specifies a single server to ping.  Can be specified multiple times to ping multiple services.
* **-f**, **--file**: Specifies the cache file to save the state of the last ping for each server.
* **-t**, **--timeout**: Specifies the timeout (minimum 1 second) used when running the ping system as per **-w <timeout>**
* **-p**, **--pixels**: Specifies the number of pixels in the neopixel display.  Exceeding the pixel count of the actual display may cause a crash.  If you set this to the number of servers you are pinging the **empty** pixel color will have no effect.
* **-a**, **--alive**: Specifies the RGB color of the pixel when a ping succeeds.  See `Commandline RGB Format`_ for an example of how to specify.
* **-d**, **--dead**: Specifies the RGB color of the pixel when a ping fails.  See `Commandline RGB Format`_ for an example of how to specify.
* **-u**, **--updating**: Specifies the RGB color of the pixel when a server has no previous status or when the update animation is occurring.  See `Commandline RGB Format`_ for an example of how to specify.
* **-e**, **--empty**: Specifies the RGB color of the pixel when updating a pixel outside the number of servers to be pinged.  See `Commandline RGB Format`_ for an example of how to specify.

Commandline RGB Format
----------------------
To make things easier to deal with, a color must be specified in an escaped double quoted string which is flattened JSON object.  For example:
::

   --alive  "{\"r\":100, \"g\":100, \"b\": 100}"


Configuration File Example
--------------------------
::

  {
    "servers": [
      "my-server",
      "192.168.0.1",
    ],
    "file": "/tmp/neopixel-healthchecker-statuses.json",
    "timeout": "1",
    "pixels": "16",
    "colors": {
      "alive": {
        "r": 10,
        "g": 10,
        "b": 10
      },
      "dead": {
        "r": 10,
        "g": 0,
        "b": 0
      },
      "updating": {
        "r": 0,
        "g": 0,
        "b": 10
      }
    }
