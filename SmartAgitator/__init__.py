# -*- coding: utf-8 -*-
from modules import cbpi, app, ActorBase
from modules.core.props import Property, StepProperty
from modules.core.step import StepBase
import os
import time
import logging

def log(s):
    print(s)
    cbpi.app.logger.info(s)

def get_config():
    config = {}
    config['smart_agitator_enabled'] = get_param("smart_agitator_enabled", "YES", "select", "Automatically turn agitator on/off when kettle heater is turned on/off?", ["YES", "NO"])
    config['smart_agitator_kettle_id'] = get_param("smart_agitator_kettle_id", "1", "text", "ID of kettle with smart agitator")
    config['smart_agitator_override'] = get_param("smart_agitator_override", "None", "text", "Name of actor whose state should prevent the smart agitator from being turned off, i.e. a timed agitator.")
    return config

def get_param(param_name, default_value, param_type, param_desc, param_opts=None):
    value = cbpi.get_config_parameter(param_name, None)
    if value is None:
        cbpi.add_config_parameter(param_name, default_value, param_type, param_desc, param_opts)
        return default_value
    return value

def get_timed_actor(name_param):
    if name_param == 'None' or name_param == '' :
        return None
    else :
        for i, value in cbpi.cache['actors'].items():
            if name_param in str(value.name) :
                return value

@cbpi.initalizer(order=999)
def init(cbpi):
    config = get_config()
    if config['smart_agitator_enabled'] != 'YES':
        log("\tSmart Agitator is not enabled.")
        return

    if 'smart_agitator_kettle_id' not in config or len(config['smart_agitator_kettle_id'].strip()) == 0:
        log("\tNo kettle ID given for smart agitator. Please set the smart_agitator_kettle_id parameter.")
        return

@cbpi.backgroundtask(key='init_smart_agitator', interval=1)
def init_smart_agitator(cbpi):
    """
    background process that checks (in interval of 1 seconds) if the kettle-assigned heater is on. 
    If so, switches on the kettle-assigned agitator. 
    :return: None
    """
    config = get_config()
    enabled = config['smart_agitator_enabled']
    kettle_id = int(config['smart_agitator_kettle_id'])
    kettle = cbpi.cache['kettle'][kettle_id]
    try :
        curr_agi = cbpi.cache.get("actors").get(int(kettle.agitator))
    except :
        curr_agi = None
    timed_actor = get_timed_actor(config['smart_agitator_override'])
    
    if not curr_agi :
        log('Smart agitator plugin is installed but kettle \#' + str(kettle_id) + ' has no agitator attached! Please choose an agitator in the kettle settings.')
        msg = {"id": len(cbpi.cache["messages"]), "type": "info", "headline": "SmartAgitator Warning", "message": "Smart agitator plugin is installed but kettle \#" + str(kettle_id) + " has no agitator attached! Please choose an agitator in the kettle settings." , "read": False}
        cbpi.cache["messages"].append(msg)
    else :
        if enabled == 'YES' and not timed_actor :

            if cbpi.cache.get("actors").get(int(kettle.heater)).state == True and cbpi.cache.get("actors").get(int(kettle.heater)).power > 0 :
                curr_agi.instance.on(100)
                cbpi.cache.get("actors").get(int(kettle.agitator)).state = True
                cbpi.emit("SWITCH_ACTOR", curr_agi)
            elif cbpi.cache.get("actors").get(int(kettle.heater)).state == False or cbpi.cache.get("actors").get(int(kettle.heater)).power < 1 :
                curr_agi.instance.off()
                cbpi.emit("SWITCH_ACTOR", curr_agi)
                cbpi.cache.get("actors").get(int(kettle.agitator)).state = False
                
        elif enabled == 'YES' and timed_actor :

            if cbpi.cache.get("actors").get(int(kettle.heater)).state == True and cbpi.cache.get("actors").get(int(kettle.heater)).power > 0 :
                curr_agi.instance.on(100)
                cbpi.cache.get("actors").get(int(kettle.agitator)).state = True
                cbpi.emit("SWITCH_ACTOR", curr_agi)
            elif cbpi.cache.get("actors").get(int(kettle.heater)).state == False or cbpi.cache.get("actors").get(int(kettle.heater)).power < 1 and timed_actor.state == False : 
                curr_agi.instance.off()
                cbpi.emit("SWITCH_ACTOR", curr_agi)
                cbpi.cache.get("actors").get(int(kettle.agitator)).state = False

@cbpi.step
class SmartAgitatorStep(StepBase):
    """
    This adds a new MashStep which you can use to toggle the SmartAgitator plugin at the beginning and end of your mash profile.
    :return: None
    """
    #Hint = Property.Text("Hint", configurable=False, defaul_value="Switches the SmartAgitator plugin ON or OFF." )
    toggle_type = Property.Select("Toggle Type", options=["On", "Off"], description="Switches the SmartAgitator plugin ON or OFF.")

    def init(self):
        '''
        Initialize step. This method is called once at the beginning of the step.
        :return: None
        '''

        config = get_config()
        kettle_id = int(config['smart_agitator_kettle_id'])
        kettle = cbpi.cache['kettle'][kettle_id]
        try :
            curr_agi = cbpi.cache.get("actors").get(int(kettle.agitator))
        except :
            curr_agi = None
        
        if not curr_agi :
            log('Smart agitator plugin is installed but kettle \#' + str(kettle_id) + ' has no agitator attached! Please choose an agitator in the kettle settings.')
            msg = {"id": len(cbpi.cache["messages"]), "type": "info", "headline": "SmartAgitator Warning", "message": "Smart agitator plugin is installed but kettle \#" + str(kettle_id) + " has no agitator attached! Please choose an agitator in the kettle settings." , "read": False}
            cbpi.cache["messages"].append(msg)
            
        if self.toggle_type == "On":
            cbpi.set_config_parameter("smart_agitator_enabled", "YES")
            log('SmatAgitatorStep executed, config parameter set to YES')
        elif self.toggle_type == "Off":
            cbpi.set_config_parameter("smart_agitator_enabled", "NO")
            cbpi.cache.get("actors").get(int(kettle.agitator)).state = False
            cbpi.emit("SWITCH_ACTOR", curr_agi)
            curr_agi.instance.off()
            log('SmatAgitatorStep executed, config parameter set to NO')
                        

    def finish(self):
        pass

    def execute(self):
        self.next()