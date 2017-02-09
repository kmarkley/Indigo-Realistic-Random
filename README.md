# Realistic Random

This is a simple plugin for random lighting control in Indigo.  Unlike other approaches, the plugin will create separate, randomized, wait-ON-wait-OFF cycles for each light it controls.  

This allows for more realistic effects. For example, a bathroom light might turn on more frequently and for shorter periods than a light in the living room.

This approach also means that each light will turn off on it's own independent schedule versus all lights turning off at once.

## Devices

The plugin defines one new type of Device, called Randomizer.  Each Randomizer device can control up to 10 relay/dimmer devices.  If you need more, just create additional Randomizers.

#### Configuration

For each of up to 10 relay or dimmer devices for this device to control:

* **Device**  
Select the device.

* **Min Delay**  
The minimum amount of time before the controlled device is turned on each cycle.

* **Max Delay**  
The maximum amount of time before the controlled device is turned on each cycle.

* **Min Duration**  
The minimum amount of time the controlled device remains on each cycle.

* **Max Duration**  
The maximum amount of time the controlled device remains on each cycle.

## Device Actions

If you don't want the randomized wait-ON-wait-OFF cycles of controlled devices to complete as scheduled, two device actions are available to override this behavior:

#### Freeze Effect

This action will cancel all cycles for controlled devices, leaving them in whatever state they are in when the action runs.  It will also turn off the randomizer device so no new cycles will be created.

#### Force All Off

Same as above, but will also turn off any controlled devices that are on.

## How to Use

* Turn the Randomizer device **ON** to begin scheduling wait-ON-wait-OFF cycles for each dimmer/relay device it controls.

* Turn the Randomizer device **OFF** to stop scheduling new cycles.  All controlled devices will complete their current cycles as scheduled.  

As a practical matter, this means you will likely want to turn the randomizer on and off in advance of when you would like the actual lights on and off.  A little trial-and-error is probably required.