# SmartAgitator plugin for  CBPi3

This plugin adds a background task to CBPi which polls the state of the kettle-assigned heater and agitator and turns on the agitator whenever the heater is ON with a power > 0.

It also adds the MashStep `SmartAgitatorStep` which you can use at the beginning and end of your mash profile to toggle the state of this plugin. I.e. I use the same kettle for mashing and for boiling. I don't need the agitator to be on while I heat up to mash-in temps, so I toggle the plugin to be ON before the first rest and turn it OFF before lautering.

## Configuration

The script adds three config parameters:

Parameter name | Values | Desc
---| :---: | ---|
smart_agitator_enabled: | `YES/NO` |
smart_agitator_kettle_id: | `int` | If you only have one kettle its ID is 1
smart_agitator_override: | `string` | The name of another agitator that should NOT be stopped when the heater is off. *


I use the same physical agitator in 2 configurations in my CBPi, once as a time-pattern-controlled actor `Timed_agitator` and once as `Agitator`. Since this plugin would shut off my agitator even if I want the time pattern to be active independently of the heater stae and power level, I have created this option to override the shut off of an active `Timed_agitator`.


# !!Be aware!!
I tried to make the script agnostic to the type of agitator, however, I only have access to one (MQTT-controlled) agitator and have no idea if yours will work!!!


