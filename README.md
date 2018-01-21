# CarMonitor
CarMonitor is a toolset to monitor and save the geographic position of a car with a RaspberryPi and a GPS sensor.
The data from the GPS sensor is saved to a local file based tracking archiv and is send to an MQTT Broker for further processing.  
A webbased app shows the current position based on the data wich is retrieved from the MQTT Broker over a WebSocket connection.

### Features
 - Reading GPS data from a GPS receiver through GPSD and Python
 - Local storage of gps tracking data saved per day
 - Transmission of the tracking data to an MQTT Broker
 - Speed adaptive processing of the position data
 - Distance adaptive processing of the position data

### Planned Features
 - Compression of the local data
 - Persistance of the MQTT Messages
 - Storage of the location data in InfluxDB 
 - Usage of a logging framework
 
### Used devices
 - Raspberry Pi 3 Model B
 - Huawei E3131 USB Modem
 - Navilock Multi GNSS Receiver u-blox
