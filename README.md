# CarMonitor
CarMonitor is a toolset to monitor and save geographic and environmental data of a car with a RaspberryPi, a GPS sensor and environment sensors.
The data from the sensors will be saved to a local file based archive and are send to an MQTT Broker for further processing.

### Features
 - Reading GPS data from a GPS receiver through GPSD and Python
 - Reading Environment data from an Enviro pHAT with Python
 - Transmission of the telemetry data to an MQTT Broker
 - Time, speed and distance check if a position update should be made
 - Time and threshold checks for environment values like temperature and pressue
 - Persistence of the MQTT Messages
 - Storage of the telemetry data in InfluxDB 

### Planned Features
 - Compression of the local data
 - Usage of a logging framework
 - Local storage of data saved per day
 
### Used devices
 - Raspberry Pi 3 Model B
 - Huawei E3131 USB Modem
 - Navilock Multi GNSS Receiver u-blox
 - Pimoroni Enviro pHAT
