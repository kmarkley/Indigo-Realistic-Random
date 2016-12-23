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

latestStateList = {
    "realisticRandomizer": (
        "nextUpdate",
        ),
    }

lightDictKeys = (
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
    def startup(self):
        self.debug = self.pluginPrefs.get("showDebugInfo",False)
        self.logger.debug(u"startup")
        if self.debug:
            self.logger.debug("Debug logging enabled")
        self.deviceList = []

    def shutdown(self):
        self.logger.debug(u"shutdown")

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        self.logger.debug(u"closedPrefsConfigUi")
        if not userCancelled:
            self.debug = valuesDict.get("showDebugInfo",False)
            if self.debug:
                self.logger.debug("Debug logging enabled")

    def validatePrefsConfigUi(self, valuesDict):
        self.logger.debug(u"validatePrefsConfigUi")
        errorsDict = indigo.Dict()
                
        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)
    
    def validateActionConfigUi(self, valuesDict, typeId, devId, runtime=False):
        self.logger.debug(u"validateActionConfigUi: " + typeId)
        errorsDict = indigo.Dict()
                
        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)

    def deviceStartComm(self, dev):
        self.logger.debug(u"deviceStartComm: "+dev.name)
        self.updateDeviceStates(dev)
        self.updateDeviceProps(dev)
        if dev.id not in self.deviceList:
            self.deviceList.append(dev.id)
    
    def deviceStopComm(self, dev):
        self.logger.debug(u"deviceStopComm: "+dev.name)
        if dev.id in self.deviceList:
            self.deviceList.remove(dev.id)
            
    def runConcurrentThread(self):
        try:
            while True:
                loopTime = time.time()
                for devId in self.deviceList:
                    dev = indigo.devices[devId]
                    if dev.onState and (dev.states["nextUpdate"] < loopTime):
                        self.updateDeviceStatus(dev)
                self.sleep(int(loopTime+10-time.time()))
        except self.StopThread:
            pass    # Optionally catch the StopThread exception and do any needed cleanup.
        
    
    ########################################
    # Device Methods
    ########################################
    
    def validateDeviceConfigUi(self, valuesDict, typeId, devId, runtime=False):
        self.logger.debug(u"validateDeviceConfigUi: " + typeId)
        errorsDict = indigo.Dict()
        
        for i in range(1,10):
            idx = '%02d' % i
            if valuesDict.get('devId'+idx,''):
                for key in lightDictKeys:
                    if valuesDict.get(key+idx,'') == '':
                        errorsDict[key+idx] = "Must not be empty"
                    elif not valuesDict.get(key+idx).isdigit():
                        errorsDict[key+idx] = "Must be a positive integer"
                    elif not ( 0 < int(valuesDict.get(key+idx)) < 481):
                        errorsDict[key+idx] = "Must be between 1 and 480"
        
        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)
    
    def didDeviceCommPropertyChange(self, origDev, newDev):
        # not necessary to re-start device on changes
        return False
    
    def updateDeviceStates(self, dev):
        if any(item not in dev.states for item in latestStateList[dev.deviceTypeId]):
            dev.stateListOrDisplayStateIdChanged()
    
    def updateDeviceProps(self, dev):
        return
        theProps = dev.pluginProps
        # update props
        if theProps != dev.pluginProps:
            dev.replacePluginPropsOnServer(theProps)
    
    def updateDeviceStatus(self,dev):
        self.logger.debug(u"updateDeviceStatus: " + dev.name)
        startTime = time.time()
        theProps = dev.pluginProps
        expireList = []
        for i in range(1,10):
            idx = '%02d' % i
            if theProps.get('devId'+idx,False):
                if (theProps.get('expires'+idx,0) < startTime):
                    randomDelay    = random.randrange(int(theProps.get('minDelay'+idx))*60, int(theProps.get('maxDelay'+idx))*60, 1)
                    randomDuration = random.randrange(int(theProps.get('minDuration'+idx))*60, int(theProps.get('maxDuration'+idx))*60, 1)
                    indigo.device.turnOn(int(theProps.get('devId'+idx)), duration=randomDuration, delay=randomDelay)
                    self.logger.info('"%s" random (delay %s, duration %s)' % (indigo.devices[int(theProps.get('devId'+idx))].name, str(datetime.timedelta(seconds=randomDelay)), str(datetime.timedelta(seconds=randomDuration))))
                    theProps['expires'+idx] = int(startTime + randomDelay + randomDuration)
                expireList.append(theProps.get('expires'+idx))
        # update device
        if theProps != dev.pluginProps:
            self.logger.debug(u"updateDeviceStatus: replacing device props")
            dev.replacePluginPropsOnServer(theProps)
            dev.updateStateOnServer(key='nextUpdate',value=min(expireList))
    
    def actionControlDimmerRelay(self, action, dev):
        self.logger.debug(u"actionControlDimmerRelay: "+dev.name)
        if action.deviceAction == indigo.kDimmerRelayAction.TurnOn:
            dev.updateStateOnServer(key='onOffState', value=True)
            self.updateDeviceStatus(dev)
        elif action.deviceAction == indigo.kDimmerRelayAction.TurnOff:
            dev.updateStateOnServer(key='onOffState', value=False)
        elif action.deviceAction == indigo.kUniversalAction.RequestStatus:
            self.updateDeviceStatus(dev)
        else:
            self.logger.error("Unknown action: "+unicode(action.deviceAction))
    
    
    ########################################
    # Action Methods
    ########################################
    
        
    
    ########################################
    # Menu Methods
    ########################################
    
    
    
    ########################################
    # Utilities
    ########################################
    