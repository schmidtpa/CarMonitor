# CarMonitor
Toolset to monitor and save the position of a car with an RaspberryPi and an GPS sensor.
The data from the GPS sensor is saved to a local file based archive and is send to an MQTT Broker for further processing.
A webbased app shows the current position based on the data read from the MQTT Broker over a WebSocket connection.
