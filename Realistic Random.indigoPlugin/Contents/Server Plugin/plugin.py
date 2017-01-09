#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# http://www.indigodomo.com

import indigo
import time
import datetime
import random


# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

###############################################################################
# globals

lightDictKeys = (
    'devId',
    'minDelay',
    'maxDelay',
    'minDuration',
    'maxDuration',
    )

################################################################################
class Plugin(indigo.PluginBase):
    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
    
    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    # Start, Stop and Config changes
    ########################################
    def startup(self):
        self.debug = self.pluginPrefs.get("showDebugInfo",False)
        self.logger.debug("startup")
        if self.debug:
            self.logger.debug("Debug logging enabled")
        self.deviceDict = dict()

    ########################################
    def shutdown(self):
        self.logger.debug("shutdown")
        self.pluginPrefs["showDebugInfo"] = self.debug

    ########################################
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        self.logger.debug("closedPrefsConfigUi")
        if not userCancelled:
            self.debug = valuesDict.get("showDebugInfo",False)
            if self.debug:
                self.logger.debug("Debug logging enabled")

    ########################################
    def validatePrefsConfigUi(self, valuesDict):
        self.logger.debug("validatePrefsConfigUi")
        errorsDict = indigo.Dict()
                
        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)
    
    ########################################
    def runConcurrentThread(self):
        try:
            while True:
                loopTime = time.time()
                for devId in self.deviceDict:
                    dev = self.deviceDict[devId]['dev']
                    if dev.onState and (self.deviceDict[devId]['nextUpdate'] < loopTime):
                        self.updateDeviceStatus(dev)
                self.sleep(int(loopTime+5-time.time()))
        except self.StopThread:
            pass    # Optionally catch the StopThread exception and do any needed cleanup.
    
    ########################################
    # Device Methods
    ########################################
    def deviceStartComm(self, dev):
        self.logger.debug("deviceStartComm: "+dev.name)
        if dev.version != self.pluginVersion:
            self.updateDeviceVersion(dev)
        if dev.id not in self.deviceDict:
            theProps = dev.pluginProps
            lightsDict = self.getLightsDict(theProps)
            self.deviceDict[dev.id] = {'dev':dev, 'nextUpdate':0, 'lightsDict':lightsDict}
    
    ########################################
    def deviceStopComm(self, dev):
        self.logger.debug("deviceStopComm: "+dev.name)
        if dev.id in self.deviceDict:
            del self.deviceDict[dev.id]
    
    ########################################
    def validateDeviceConfigUi(self, valuesDict, typeId, devId, runtime=False):
        self.logger.debug("validateDeviceConfigUi: " + typeId)
        errorsDict = indigo.Dict()
        
        for idx in ("%02d"%i for i in range(1,11)):
            if valuesDict.get('devId'+idx,''):
                for key in lightDictKeys[1:]:
                    if valuesDict.get(key+idx,'') == '':
                        errorsDict[key+idx] = "Must not be empty"
                    elif not valuesDict.get(key+idx).isdigit():
                        errorsDict[key+idx] = "Must be a positive integer"
                    elif not ( 0 < int(valuesDict.get(key+idx)) < 481):
                        errorsDict[key+idx] = "Must be between 1 and 480"
        
        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)
    
    ########################################
    def updateDeviceVersion(self, dev):
        theProps = dev.pluginProps
        # update states
        dev.stateListOrDisplayStateIdChanged()
        # check for props
        for idx in ("%02d"%i for i in range(1,11)):
            vals = {}
            for key in lightDictKeys:
                if key+idx not in theProps:
                    theProps[key+idx] = ''
        # push to server
        theProps["version"] = self.pluginVersion
        dev.replacePluginPropsOnServer(theProps)
    
    ########################################
    def updateDeviceStatus(self,dev):
        self.logger.debug("updateDeviceStatus: " + dev.name)
        startTime = time.time()
        expireList = []
        for idx, light in self.deviceDict[dev.id]['lightsDict'].iteritems():
            if light['devId']:
                if light.get('expires',0) < startTime:
                    randomDelay    = random.randrange(light['minDelay']*60, light['maxDelay']*60, 1)
                    randomDuration = random.randrange(light['minDuration']*60, light['maxDuration']*60, 1)
                    self.logger.info('"%s" random (delay %s, duration %s)' % (indigo.devices[light['devId']].name, str(datetime.timedelta(seconds=randomDelay)), str(datetime.timedelta(seconds=randomDuration))))
                    indigo.device.turnOn(light['devId'], duration=randomDuration, delay=randomDelay)
                    expire = int(startTime + randomDelay + randomDuration)
                    self.deviceDict[dev.id]['lightsDict'][idx]['expires'] = expire
                else:
                    expire = light['expires']
                expireList.append(expire)
        # don't update again until at least one cycle completes
        self.deviceDict[dev.id]['nextUpdate'] = min(expireList)
    
    ########################################
    # Action Methods
    ########################################
    def validateActionConfigUi(self, valuesDict, typeId, devId, runtime=False):
        self.logger.debug("validateActionConfigUi: " + typeId)
        errorsDict = indigo.Dict()
                
        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)

    ########################################
    def actionControlDimmerRelay(self, action, dev):
        self.logger.debug("actionControlDimmerRelay: "+dev.name)
        if action.deviceAction == indigo.kDimmerRelayAction.TurnOn:
            self.logger.info('"%s" on' % dev.name)
            dev.updateStateOnServer(key='onOffState', value=True)
            self.deviceDict[dev.id]['dev'].refreshFromServer()
            self.updateDeviceStatus(dev)
        elif action.deviceAction == indigo.kDimmerRelayAction.TurnOff:
            self.logger.info('"%s" off' % dev.name)
            dev.updateStateOnServer(key='onOffState', value=False)
            self.deviceDict[dev.id]['dev'].refreshFromServer()
        elif action.deviceAction == indigo.kUniversalAction.RequestStatus:
            self.logger.info('"%s" status update' % dev.name)
            if dev.onState:
                self.updateDeviceStatus(dev)
        else:
            self.logger.error("Unknown action: "+unicode(action.deviceAction))
    
    ########################################
    # Menu Methods
    ########################################
    def toggleDebug(self):
        if self.debug:
            self.logger.debug("Debug logging disabled")
            self.debug = False
        else:
            self.debug = True
            self.logger.debug("Debug logging enabled")
        
    
    ########################################
    # Utilities
    ########################################
    def getLightsDict(self, theProps):
        lightsDict={}
        for idx in ("%02d"%i for i in range(1,11)):
            vals = {}
            for key in lightDictKeys:
                if theProps.get(key+idx,''):
                    vals[key] = int(theProps.get(key+idx))
                else:
                    vals[key] = 0
            lightsDict[idx] = vals
        return lightsDict
