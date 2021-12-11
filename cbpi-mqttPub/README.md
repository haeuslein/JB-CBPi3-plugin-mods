**This is a modification of the CBPi3 plugin ``cbpi-mqttPub`` by InnuendoPi (https://github.com/InnuendoPi/cbpi-mqttPub) so most, if not all, the credit goes to him!**

Any hate because this mod broke your setup is justly directed at me (even though you are somewhat to blame because you copied untested code from the internet... ;-), so run this in a DEV environment first).


_It woks on my machine_ - but I give no gurantees!!!!

# What did I do?

## I added the class ``MQTTActor_timed``
This allows you to run an MQTTActor in a time pattern, e.g. run every 5 min for 30 sec. I use this for my agitator.

## I added background task ``@cbpi.backgroundtask(key='mqtt_pubb`` which publishes a few CBPi internals to MQTT:

```
Fermenter state: ON/OFF
Fermenter target temp: int
Fermenter brew name: string (whatever you typed in as brewname on the fermentation screen)
brewery name: string (whatever you called your CBPi instance when you set it up)
```

This depends on the existence of a fermenter in CBPi - I have not tested what happens if it doesn't find one...

The MQTT topic can be set by editing the string variable 'topic'.

I pick these values up in a seperate NodeRED installation which monitors my fermenter state and temps. All actors and sensor that are part of my fermenter setup are already sending their data via MQTT so they do not show up here. If needed, it is probably easy to add those to this publishing task.


# The following is the original readme.md for this plugin by InnuendoPI:


# MQTT-Publisch für CraftBeerPi 3.0

Plugin für CraftbeerPi zur Anbindung von MQTT Sensoren und Aktoren. MQTT-Pub ersetzt cbpi-mqttCompressor und ist für Verwendung von MQTTDevice2 erforderlich. Das Plugin basiert auf dem CraftbeerPi3 MQTT Basis Plugin.

## Installation

Das Plugin muss in das CraftbeerPi3 Verzeichnis ..\craftbeerpi3\modules\plugins\cbpi-mqttPub kopiert werden.

# MQTT Plugin for CraftBeerPi 3.0

This plugins allows to connect to an MQTT Message broker to receive sensor data and invoke actors.

## Installation

### Install missing python lib
After installation please install python MQTT lib paho

```pip install paho-mqtt```

https://pypi.python.org/pypi/paho-mqtt/1.1

### Install MQTT message broker

Second step is to install an MQTT message broker on your Raspberry Pi.
An open source message broker is mosquitto (https://mosquitto.org/)

```
sudo apt-get update
sudo apt-get install mosquitto

# Furhter commands to control mosquitto service
sudo service mosquitto status
sudo service mosquitto stop
sudo service mosquitto start
```

The current version don't support username and password log for the mqtt broker

# MQTT Test Client 
A nice MQTT test client is mqtt.fx http://www.mqttfx.org/

# Plugin config

## MQTT Sensor

- Enter the message topic
- If the data in the payload is in a dictionary, specify the path in "Payload dictionary" with '.' seperators. EG
  - msg = { "Name":"MySensor", "Sensor": {"Value": 32 , "Type" : "1-wire"}
  - "Payload Dict" = Sensor.Value
- If you data is raw eg (mosquitto_pub -d -t temperture -m 32), leave "Payload Dictionary" Blank
- Enter prefered unit up to 3 chars
