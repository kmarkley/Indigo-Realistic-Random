#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# http://www.indigodomo.com

import indigo
import time
import datetime
import random
from ghpu import GitHubPluginUpdater


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

k_updateCheckHours = 24

################################################################################
class Plugin(indigo.PluginBase):

    #-------------------------------------------------------------------------------
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.updater = GitHubPluginUpdater(self)

    def __del__(self):
        indigo.PluginBase.__del__(self)

    #-------------------------------------------------------------------------------
    # Start, Stop and Config changes
    #-------------------------------------------------------------------------------
    def startup(self):
        self.nextCheck = self.pluginPrefs.get('nextUpdateCheck',0)
        self.debug = self.pluginPrefs.get("showDebugInfo",False)
        self.logger.debug("startup")
        if self.debug:
            self.logger.debug("Debug logging enabled")
        self.deviceDict = dict()

    #-------------------------------------------------------------------------------
    def shutdown(self):
        self.logger.debug("shutdown")
        self.pluginPrefs['nextUpdateCheck'] = self.nextCheck
        self.pluginPrefs["showDebugInfo"] = self.debug

    #-------------------------------------------------------------------------------
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        self.logger.debug("closedPrefsConfigUi")
        if not userCancelled:
            self.debug = valuesDict.get("showDebugInfo",False)
            if self.debug:
                self.logger.debug("Debug logging enabled")

    #-------------------------------------------------------------------------------
    def runConcurrentThread(self):
        try:
            while True:
                loopTime = time.time()
                for devId, dev in self.deviceDict.items():
                    dev.update()
                if loopTime > self.nextCheck:
                    self.checkForUpdates()
                self.sleep(loopTime+5-time.time())
        except self.StopThread:
            pass

    #-------------------------------------------------------------------------------
    # Device Methods
    #-------------------------------------------------------------------------------
    def deviceStartComm(self, dev):
        self.logger.debug("deviceStartComm: "+dev.name)
        if dev.version != self.pluginVersion:
            self.updateDeviceVersion(dev)
        if dev.configured:
            self.deviceDict[dev.id] = self.Randomizer(dev, self)

    #-------------------------------------------------------------------------------
    def deviceStopComm(self, dev):
        self.logger.debug("deviceStopComm: "+dev.name)
        if dev.id in self.deviceDict:
            #self.deviceDict[dev.id].cancel()
            del self.deviceDict[dev.id]

    #-------------------------------------------------------------------------------
    def validateDeviceConfigUi(self, valuesDict, typeId, devId, runtime=False):
        self.logger.debug("validateDeviceConfigUi: " + typeId)
        errorsDict = indigo.Dict()

        lightsList = []
        for idx in ("{:0>2d}".format(i) for i in range(1,11)):
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

    #-------------------------------------------------------------------------------
    def updateDeviceVersion(self, dev):
        theProps = dev.pluginProps
        # update states
        dev.stateListOrDisplayStateIdChanged()
        # check for props
        for index in range(1,11):
            indexString = "{:0>2d}".format(index)
            for key in lightDictKeys:
                if key+indexString not in theProps:
                    theProps[key+indexString] = ''
        # push to server
        theProps["version"] = self.pluginVersion
        dev.replacePluginPropsOnServer(theProps)

    #-------------------------------------------------------------------------------
    # Action Methods
    #-------------------------------------------------------------------------------
    def actionControlDimmerRelay(self, action, dev):
        self.logger.debug("actionControlDimmerRelay: "+dev.name)
        randomizer = self.deviceDict[dev.id]
        # TURN ON
        if action.deviceAction == indigo.kDimmerRelayAction.TurnOn:
            randomizer.onState = True
        # TURN OFF
        elif action.deviceAction == indigo.kDimmerRelayAction.TurnOff:
            randomizer.onState = False
        # TOGGLE
        elif action.deviceAction == indigo.kDimmerRelayAction.Toggle:
            randomizer.onState = not randomizer.onState
        # STATUS REQUEST
        elif action.deviceAction == indigo.kUniversalAction.RequestStatus:
            self.logger.info('"{}" status update'.format(dev.name))
            randomizer.update()
        # UNKNOWN
        else:
            self.logger.debug('"{}" {} request ignored'.format(dev.name, unicode(action.deviceAction)))

    #-------------------------------------------------------------------------------
    def freezeRandomizerEffect(self, action):
        try:
            self.deviceDict[action.deviceId].cancel(False)
        except:
            self.logger.error('device "{}" not available'.format(action.deviceId))

    #-------------------------------------------------------------------------------
    def forceRandomizerOff(self, action):
        try:
            self.deviceDict[action.deviceId].cancel(True)
        except:
            self.logger.error('device "{}" not available'.format(action.deviceId))

    #-------------------------------------------------------------------------------
    # Menu Methods
    #-------------------------------------------------------------------------------
    def checkForUpdates(self):
        try:
            self.updater.checkForUpdate()
        except Exception as e:
            msg = 'Check for update error.  Next attempt in {} hours.'.format(k_updateCheckHours)
            if self.debug:
                self.logger.exception(msg)
            else:
                self.logger.error(msg)
                self.logger.debug(e)
        self.nextCheck = time.time() + k_updateCheckHours*60*60

    #-------------------------------------------------------------------------------
    def updatePlugin(self):
        self.updater.update()

    #-------------------------------------------------------------------------------
    def forceUpdate(self):
        self.updater.update(currentVersion='0.0.0')

    #-------------------------------------------------------------------------------
    def toggleDebug(self):
        if self.debug:
            self.logger.debug("Debug logging disabled")
            self.debug = False
        else:
            self.debug = True
            self.logger.debug("Debug logging enabled")

    #-------------------------------------------------------------------------------
    # Menu Callbacks
    #-------------------------------------------------------------------------------
    def getRelayDimmerDeviceList(self, filter="", valuesDict=None, typeId="", targetId=0):
        devList = []
        excludeList  = [dev.id for dev in indigo.devices.iter(filter='self')]
        for dev in indigo.devices.iter(filter='indigo.relay, indigo.dimmer'):
            if not dev.id in excludeList:
                devList.append((dev.id, dev.name))
        devList.append((0,"- none -"))
        return devList

    ###############################################################################
    # Classes
    ###############################################################################
    class Randomizer(object):

        #-------------------------------------------------------------------------------
        def __init__(self, instance, plugin):
            self.dev        = instance
            self.name       = self.dev.name
            self.props      = self.dev.pluginProps
            self.states     = self.dev.states
            self.nextUpdate = 0

            self.logger     = plugin.logger

            self.lightsList = list()
            for index in range(1,11):
                try:
                    self.lightsList.append(self.ControlledLight(self.props, index, self))
                except:
                    pass

        #-------------------------------------------------------------------------------
        def update(self):
            if self.onState:
                for light in self.lightsList:
                    light.update()
                self.nextUpdate = min(light.expire for light in self.lightsList)

        #-------------------------------------------------------------------------------
        def cancel(self, turnOff=False):
            self.onState = False
            for light in self.lightsList:
                light.cancel(turnOff)

        #-------------------------------------------------------------------------------
        # Class Properties
        #-------------------------------------------------------------------------------
        def onStateGet(self):
            return self.states['onOffState']

        def onStateSet(self,newState):
            if newState != self.onState:
                self.logger.info('"{}" {}'.format(self.dev.name, ['off','on'][newState]))
                self.dev.updateStateOnServer(key='onOffState', value=newState)
                self.states = self.dev.states
                if newState:
                    self.update()

        onState = property(onStateGet, onStateSet)

        ###############################################################################
        class ControlledLight(object):

            #-------------------------------------------------------------------------------
            def __init__(self, props, index, parent):
                indexString     = "{:0>2d}".format(index)
                self.id         = int(props.get('devId'+indexString,'0'))
                self.refresh()
                self.minDel     = int(props.get('minDelay'+indexString,'5'))
                self.maxDel     = int(props.get('maxDelay'+indexString,'60'))
                self.minDur     = int(props.get('minDuration'+indexString,'5'))
                self.maxDur     = int(props.get('maxDuration'+indexString,'60'))
                self.expire     = 0
                self.logger     = parent.logger

            #-------------------------------------------------------------------------------
            def refresh(self):
                self.dev        = indigo.devices[self.id]
                self.name       = self.dev.name
                self.onState    = self.dev.onState

            #-------------------------------------------------------------------------------
            def update(self):
                if self.expire < time.time():
                    self.refresh()
                    randomDelay     = random.randrange(self.minDel*60, self.maxDel*60, 1)
                    randomDuration  = random.randrange(self.minDur*60, self.maxDur*60, 1)
                    delayStr        = ['delay {}'.format(datetime.timedelta(seconds=randomDelay)), 'already on'][self.onState]
                    durationStr     = 'duration {}'.format(datetime.timedelta(seconds=randomDuration))
                    self.logger.info('"{}" random ({}, {})'.format(self.name, delayStr, durationStr))
                    if self.onState:
                        indigo.device.turnOff(self.id, delay=randomDuration)
                    else:
                        indigo.device.turnOn(self.id, duration=randomDuration, delay=randomDelay)
                    self.expire = time.time() + randomDelay + randomDuration

            #-------------------------------------------------------------------------------
            def cancel(self, turnOff=False):
                self.refresh()
                self.expire = 0
                self.logger.debug('remove delayed actions for "{}"'.format(self.name))
                indigo.device.removeDelayedActions(self.id)
                if self.onState and turnOff:
                    self.logger.debug('turn off "{}"'.format(self.name))
                    indigo.device.turnOff(self.id)
