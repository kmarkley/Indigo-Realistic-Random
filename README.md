# Realistic Random

This is a simple plugin for random lighting control in Indigo.  Unlike other approaches, the plugin will create separate, randomized, WAIT-ON-WAIT-OFF cycles for each light it controls.  

This allows for more realistic effects. For example, you may want the bathroom light to have several widely-varying off periods and short on periods, while ceiling lights remain on for very long periods with only the start and end time randomized.

This approach also means that each device will turn off on it's own idependent schedule versus all devices turning off at once.

## Devices

The plugin defines one new type of Device, called Realistic Randomizer.  Each Realistic Randomizer device can control up to 10 relay/dimmer devices.  If you need more, just create additional Randomizers.

#### Configuration

* **Device** (1-10)  
Define up to 10 relay or dimmer devices for this device to control.

* **Min Delay** (1-10)  
The minimum amount of time before the controlled device is tuned on each cycle.

* **Max Delay** (1-10)  
The maximum amount of time before the controlled device is tuned on each cycle.

* **Min Duration** (1-10)  
The minimum amount of time the controlled device remains on each cycle.

* **Min Duration** (1-10)  
The maximum amount of time the controlled device remains on each cycle.


#### States

* **Next Update**  
Seconds after epoch when the next update is scheduled.  Used internally.


## How to Use

* Turn the Realistic Randomizer device on to begin scheuling WAIT-ON-WAIT-OFF cycles for each dimmer/relay device it controls.

* Turn the Realsitic Randomizer device off to stop scheduling new cycles.  All controlled devices will complete their current cycles as scheduled.  

As a practical matter, this means you will likely want to turn the randomizer on and off in advance of when you would like the actual lights on and off.  A little trial-and-error may be required.