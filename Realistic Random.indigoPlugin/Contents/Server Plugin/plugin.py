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
                    if self.deviceDict[devId]['dev'].states['onOffState'] and (self.deviceDict[devId]['nextUpdate'] < loopTime):
                        self.updateDeviceStatus(devId)
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
        self.deviceDict[dev.id] = {'dev':dev, 'nextUpdate':0, 'lightsDict':self.getLightsDict(dev)}
    
    ########################################
    def deviceStopComm(self, dev):
        self.logger.debug("deviceStopComm: "+dev.name)
        if dev.id in self.deviceDict:
            if dev.states['onOffState']:
                self.cancelCycles(dev.id, False)
            del self.deviceDict[dev.id]
    
    ########################################
    def validateDeviceConfigUi(self, valuesDict, typeId, devId, runtime=False):
        self.logger.debug("validateDeviceConfigUi: " + typeId)
        errorsDict = indigo.Dict()
        
        lightsList = []
        for idx in ("%02d"%i for i in range(1,11)):
            lightId = valuesDict.get('devId'+idx,'')
            if lightId:
                if lightId in lightsList:
                    errorsDict['devId'+idx] = "Duplicate device"
                else:
                    lightsList.append(lightId)
                    for key in lightDictKeys[1:]:
                        if valuesDict.get(key+idx,'') == '':
                            errorsDict[key+idx] = "Must not be empty"
                        elif not valuesDict.get(key+idx).isdigit():
                            errorsDict[key+idx] = "Must be a positive integer"
                        elif not ( 0 < int(valuesDict.get(key+idx)) < 481):
                            errorsDict[key+idx] = "Must be between 1 and 480"
        
        if len(errorsDict) > 0:
            self.logger.debug('validate device config error: \n%s' % str(errorsDict))
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)
    
    ########################################
    def updateDeviceVersion(self, dev):
        theProps = dev.pluginProps
        # update states
        dev.stateListOrDisplayStateIdChanged()
        # check for props
        for idx in ("%02d"%i for i in range(1,11)):
            for key in lightDictKeys:
                if key+idx not in theProps:
                    theProps[key+idx] = ''
        # push to server
        theProps["version"] = self.pluginVersion
        dev.replacePluginPropsOnServer(theProps)
    
    ########################################
    def updateDeviceStatus(self, devId):
        self.logger.debug("updateDeviceStatus: " + self.deviceDict[devId]['dev'].name)
        startTime = time.time()
        expireList = []
        for idx, lightProps in self.deviceDict[devId]['lightsDict'].iteritems():
            if lightProps['expires'] < startTime:
                light = indigo.devices[lightProps['devId']]
                randomDelay    = [random.randrange(lightProps['minDelay']*60, lightProps['maxDelay']*60, 1), 0][light.onState]
                randomDuration = random.randrange(lightProps['minDuration']*60, lightProps['maxDuration']*60, 1)
                delayStr       = ['delay %s' % str(datetime.timedelta(seconds=randomDelay)), 'already on'][light.onState]
                durationStr    = 'duration %s' % str(datetime.timedelta(seconds=randomDuration))
                self.logger.info('"%s" random (%s, %s)' % (light.name, delayStr, durationStr))
                if light.onState:
                    indigo.device.turnOff(light.id, delay=randomDuration)
                else:
                    indigo.device.turnOn(light.id, duration=randomDuration, delay=randomDelay)
                expire = int(startTime + randomDelay + randomDuration)
                self.deviceDict[devId]['lightsDict'][idx]['expires'] = expire
            else:
                expire = lightProps['expires']
            expireList.append(expire)
        # don't update again until at least one cycle completes
        self.deviceDict[devId]['nextUpdate'] = min(expireList)
    
    ########################################
    # Action Methods
    ########################################
    def validateActionConfigUi(self, valuesDict, typeId, devId, runtime=False):
        self.logger.debug("validateActionConfigUi: " + typeId)
        errorsDict = indigo.Dict()
                
        if len(errorsDict) > 0:
            self.logger.debug('validate action config error: \n%s' % str(errorsDict))
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)

    ########################################
    def actionControlDimmerRelay(self, action, dev):
        self.logger.debug("actionControlDimmerRelay: "+dev.name)
        # TURN ON
        if action.deviceAction == indigo.kDimmerRelayAction.TurnOn:
            self.setDeviceState(dev.id, True)
        # TURN OFF
        elif action.deviceAction == indigo.kDimmerRelayAction.TurnOff:
            self.setDeviceState(dev.id, False)
        # TOGGLE
        elif action.deviceAction == indigo.kDimmerRelayAction.Toggle:
            self.setDeviceState(dev.id, not dev.states['onOffState'])
        # STATUS REQUEST
        elif action.deviceAction == indigo.kUniversalAction.RequestStatus:
            self.logger.info('"%s" status update' % dev.name)
            if dev.states['onOffState']:
                self.updateDeviceStatus(dev.id)
        # UNKNOWN
        else:
            self.logger.debug('"%s" %s request ignored' % (dev.name, unicode(action.deviceAction)))
    
    ########################################
    def freezeRandomizerEffect(self, action):
        if action.deviceId in self.deviceDict:
            self.setDeviceState(action.deviceId, False)
            self.cancelCycles(action.deviceId, False)
        else:
            self.logger.error('device "%s" not available' % action.deviceId)
    
    ########################################
    def forceRandomizerOff(self, action):
        if action.deviceId in self.deviceDict:
            self.setDeviceState(action.deviceId, False)
            self.cancelCycles(action.deviceId, True)
        else:
            self.logger.error('device "%s" not available' % action.deviceId)
    
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
    # Menu Callbacks
    ########################################
    def getRelayDimmerDeviceList(self, filter="", valuesDict=None, typeId="", targetId=0):
        devList = []
        excludeList  = [dev.id for dev in indigo.devices.iter(filter='self')]
        for dev in indigo.devices.iter(filter='indigo.relay, indigo.dimmer'):
            if not dev.id in excludeList:
                devList.append((dev.id, dev.name))
        devList.append((0,"- none -"))
        return devList        
        
    ########################################
    # Utilities
    ########################################
    def getLightsDict(self, dev):
        theProps = dev.pluginProps
        lightsDict={}
        for idx in ("%02d"%i for i in range(1,11)):
            lightProps = {}
            for key in lightDictKeys:
                if theProps.get(key+idx,''):
                    lightProps[key] = int(theProps[key+idx])
                else:
                    lightProps[key] = 0
            lightProps['expires'] = 0
            if lightProps['devId']:
                lightsDict[idx] = lightProps
        return lightsDict
    
    def cancelCycles(self, devId, lightsOff=False):
        self.logger.debug("cancelCycles: " + self.deviceDict[devId]['dev'].name)
        self.logger.info('"%s" %s' % (self.deviceDict[devId]['dev'].name, ['freeze effect','force all off'][lightsOff]))
        for idx, lightProps in self.deviceDict[devId]['lightsDict'].iteritems():
            light = indigo.devices[lightProps['devId']]
            self.logger.debug('remove delayed actions for "%s"' % light.name)
            indigo.device.removeDelayedActions(light.id)
            if lightsOff and light.onState:
                self.logger.debug('turn off "%s"' % light.name)
                indigo.device.turnOff(light.id)
            self.deviceDict[devId]['lightsDict'][idx]['expires'] = 0
        self.deviceDict[devId]['nextUpdate'] = 0
    
    def setDeviceState(self, devId, onOffState):
        dev = self.deviceDict[devId]['dev']
        if dev.states['onOffState'] != onOffState:
            self.logger.info('"%s" %s' % (dev.name, ['off','on'][onOffState]))
            dev.updateStateOnServer(key='onOffState', value=onOffState)
            if onOffState:
                self.updateDeviceStatus(devId)
