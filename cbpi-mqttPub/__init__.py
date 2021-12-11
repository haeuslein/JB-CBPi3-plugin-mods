# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
from eventlet import Queue
from modules import cbpi, app, ActorBase
from modules.core.hardware import SensorActive
import json
import os
import re
import threading
import time
import logging
from modules.core.props import Property
from modules.fermenter import FermenterView

from datetime import datetime, timedelta

cbpi.MQTTActor_Compressors = []

q = Queue()


def on_connect(client, userdata, flags, rc):
    print("MQTT Connected" + str(rc))

def log(s):
    print(s)
    cbpi.app.logger.info(s)

class MQTTThread (threading.Thread):

    def __init__(self, server, port, username, password, tls):
        threading.Thread.__init__(self)
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.tls = tls

    client = None

    def run(self):
        self.client = mqtt.Client()
        self.client.on_connect = on_connect

        if self.username != "username" and self.password != "password":
            self.client.username_pw_set(self.username, self.password)

        if self.tls.lower() == 'true':
            self.client.tls_set_context(context=None)

        self.client.connect(str(self.server), int(self.port), 60)
        self.client.loop_forever()


@cbpi.actor
class MQTTActor(ActorBase):
    topic = Property.Text("Topic", configurable=True,
                          default_value="", description="MQTT TOPIC")
    pPower = 100

    def on(self, power):
        if power is not None:
            if power != self.pPower:
                power = min(100, power)
                power = max(0, power)
                self.pPower = int(power)
        self.api.cache["mqtt"].client.publish(self.topic, payload=json.dumps(
            {"state": "on", "power": self.pPower}), qos=2, retain=True)

    def off(self):
        self.api.cache["mqtt"].client.publish(
            self.topic, payload=json.dumps({"state": "off"}), qos=2, retain=True)

    def set_power(self, power):
        self.on(power)


@cbpi.actor
class MQTTActor_timed(ActorBase):
    topic = Property.Text("Topic", configurable=True,
                          default_value="", description="MQTT TOPIC")
    pPower = 100
    time_start = Property.Number("Actor on for [sec]", configurable=True, description="How long should the Actor run in each interval.")
    time_stop  = Property.Number("Turn on every [sec]", configurable=True, description="Actor should run every x seconds.")
    timed_start = 0

    def on(self, power):
        if power is not None:
            if power != self.pPower:
                power = min(100, power)
                power = max(0, power)
                self.pPower = int(power)
        self.api.cache["mqtt"].client.publish(self.topic, payload=json.dumps(
            {"state": "on", "power": self.pPower}), qos=2, retain=True)

    def off(self):
        self.api.cache["mqtt"].client.publish(
            self.topic, payload=json.dumps({"state": "off"}), qos=2, retain=True)

    def set_power(self, power):
        self.on(power)

    def timedActor (self):
        while (self.timed_start == 1):
            self.api.cache.get("actors").get(int(self.id)).timer =  int(time.time()) + int(self.time_start) -1
            self.api.switch_actor_on(self.id)
            self.sleep(int(self.time_start))

            self.api.cache.get("actors").get(int(self.id)).timer = int(time.time()) + int(self.time_stop) -1
            self.api.switch_actor_off(self.id)
            self.sleep(int(self.time_stop))

        else:
            self.api.cache.get("actors").get(int(self.id)).timer =  None
            self.api.switch_actor_on(self.id)
            self.api.switch_actor_off(self.id)

    @cbpi.action("Start Actor Timer")
    def start(self):
        self.timed_start = 1
        self.api.notify(headline="Timed MQTTActor", message="Timed MQTTActor started", type="info")
        self.timedActor()


    @cbpi.action("Stop Actor Timer")
    def stop(self):
        self.api.notify(headline="Timed MQTTActor", message="Timed MQTTActor will be stopped after current timer ends.", type="info")
        self.timed_start = 0


@cbpi.actor
class ESPEasyMQTT(ActorBase):
    topic = Property.Text("Topic", configurable=True,
                          default_value="", description="MQTT TOPIC")

    def on(self, power=100):
        self.api.cache["mqtt"].client.publish(
            self.topic, payload=1, qos=2, retain=True)

    def off(self):
        self.api.cache["mqtt"].client.publish(
            self.topic, payload=0, qos=2, retain=True)


@cbpi.sensor
class MQTT_SENSOR(SensorActive):
    a_topic = Property.Text("Topic", configurable=True,
                            default_value="", description="MQTT TOPIC")
    b_payload = Property.Text("Payload Dictioanry", configurable=True, default_value="",
                              description="Where to find msg in payload, leave blank for raw payload")
    c_unit = Property.Text("Unit", configurable=True,
                           default_value="", description="Units to display")

    last_value = None

    def init(self):
        self.topic = self.a_topic
        if self.b_payload == "":
            self.payload_text = None
        else:
            self.payload_text = self.b_payload.split('.')
        self.unit = self.c_unit[0:3]

        SensorActive.init(self)
        def on_message(client, userdata, msg):

            try:
                print "payload " + msg.payload
                json_data = json.loads(msg.payload)
                # print json_data
                val = json_data
                if self.payload_text is not None:
                    for key in self.payload_text:
                        val = val.get(key, None)
                # print val
                if isinstance(val, (int, float, basestring)):
                    q.put({"id": on_message.sensorid, "value": val})
            except Exception as e:
                print e
        on_message.sensorid = self.id
        self.api.cache["mqtt"].client.subscribe(self.topic)
        self.api.cache["mqtt"].client.message_callback_add(
            self.topic, on_message)

    def get_value(self):
        return {"value": round(float(self.last_value), 2), "unit": self.unit}

    def get_unit(self):
        return self.unit

    def stop(self):
        self.api.cache["mqtt"].client.unsubscribe(self.topic)
        SensorActive.stop(self)

    def execute(self):
        '''
        Active sensor has to handle his own loop
        :return:
        '''
        self.sleep(5)


@cbpi.actor
class MQTTActor_Compressor(ActorBase):
    topic = Property.Text("Topic", configurable=True,
                          default_value="", description="MQTT TOPIC")
    delay = Property.Number(
        "Compressor Delay", configurable=True, default_value=10, description="minutes")
    compressor_on = False
    compressor_wait = datetime.utcnow()
    delayed = False

    def init(self):
        super(MQTTActor_Compressor, self).init()
        cbpi.MQTTActor_Compressors += [self]

    def on(self, power=100):
        if datetime.utcnow() >= self.compressor_wait:
            self.compressor_on = True
            self.api.cache["mqtt"].client.publish(self.topic, payload=json.dumps(
                {"state": "on", "power": "100"}), qos=2, retain=True)
            self.delayed = False
        else:
            cbpi.app.logger.info("Delaying Turing on Compressor")
            self.delayed = True

    def off(self):
        if self.compressor_on:
            self.compressor_on = False
            self.compressor_wait = datetime.utcnow() + timedelta(minutes=int(self.delay))
        self.delayed = False
        self.api.cache["mqtt"].client.publish(
            self.topic, payload=json.dumps({"state": "off"}), qos=2, retain=True)


@cbpi.initalizer(order=0)
def initMQTT(app):

    server = app.get_config_parameter("MQTT_SERVER", None)
    if server is None:
        server = "localhost"
        cbpi.add_config_parameter(
            "MQTT_SERVER", "localhost", "text", "MQTT Server")

    port = app.get_config_parameter("MQTT_PORT", None)
    if port is None:
        port = "1883"
        cbpi.add_config_parameter(
            "MQTT_PORT", "1883", "text", "MQTT Sever Port")

    username = app.get_config_parameter("MQTT_USERNAME", None)
    if username is None:
        username = "username"
        cbpi.add_config_parameter(
            "MQTT_USERNAME", "username", "text", "MQTT username")

    password = app.get_config_parameter("MQTT_PASSWORD", None)
    if password is None:
        password = "password"
        cbpi.add_config_parameter(
            "MQTT_PASSWORD", "password", "text", "MQTT password")

    tls = app.get_config_parameter("MQTT_TLS", None)
    if tls is None:
        tls = "false"
        cbpi.add_config_parameter("MQTT_TLS", "false", "text", "MQTT TLS")

    app.cache["mqtt"] = MQTTThread(server, port, username, password, tls)
    app.cache["mqtt"].daemon = True
    app.cache["mqtt"].start()

    def mqtt_reader(api):
        while True:
            try:
                m = q.get(timeout=0.1)
                api.cache.get("sensors")[m.get(
                    "id")].instance.last_value = m.get("value")
                api.receive_sensor_value(m.get("id"), m.get("value"))
            except:
                pass

    cbpi.socketio.start_background_task(target=mqtt_reader, api=app)


@cbpi.backgroundtask(key="update_MQTTActor_compressors", interval=5)
def update_MQTTActor_compressors(api):
    for compressor in cbpi.MQTTActor_Compressors:
        if compressor.delayed and datetime.utcnow() >= compressor.compressor_wait:
            compressor.on()

@cbpi.backgroundtask(key='mqtt_pub', interval=15)
def mqtt_pub(api):
    """
    background process that reads all passive sensors in interval of 5 second
    :return: None
    """

    for i, value in cbpi.cache['kettle'].items():
        topic = 'MQTTDevice/kettle/' + str(i)
        data = {
            'id': i,
            'he': cbpi.cache.get("actors").get(int(value.heater)).config["topic"],
            'te': cbpi.get_sensor_value(value.sensor),
            'tt': value.target_temp
        }
        api.cache["mqtt"].client.publish(
            topic, payload=json.dumps(data, ensure_ascii=False), qos=0, retain=False)

@cbpi.backgroundtask(key='mqtt_pubb', interval=15)
def mqtt_pubb(api):
    """
    background process that reads the fermenter state and target temp in interval of 5 second
    :return: None
    """

    fermenter = FermenterView().get_fermenter(1)
    topic = 'MQTTDevice/fermenter/' + fermenter.name
    #beer = fermenter.brewname

    if fermenter.state:
        ferm_state = 'ON'
        #log(ferm_state + ' -- this is ON if fermenter was ON')
    else :
        ferm_state = 'OFF'
        #log(ferm_state + ' -- this is OFF if fermenter was OFF')
    pl = {'state': ferm_state, 'targetTemp:': fermenter.target_temp, 'brewery': api.get_config_parameter("brewery_name", None), 'beer': fermenter.brewname}
    try :
        api.cache["mqtt"].client.publish(topic, payload=json.dumps(pl, ensure_ascii=False), qos=0, retain=False)
        #log('fermenter state should be published -- ' + fermenter.brewname)
    except :
        log('failed to publish fermenter state')