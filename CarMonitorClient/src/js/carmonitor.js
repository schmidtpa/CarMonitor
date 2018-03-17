function CarMonitor(serverHostname, serverPort, mapStart) {
	
	var serverHostname = serverHostname;
	var serverPort = serverPort;
	var mapStart = mapStart;
	
	var cars;
	var map;
	var mqtt;

	this.start = function(){
		// setup car array
		cars = [];
		
		// setup UI
		$("#map").hide();
		$("#loginDialog").show();
		$("#loginButton").click(this.connect());
		
		// setup map
		map = L.map('map',{
			center: mapStart,
			zoom: 14
		});
		
		attribution = '&copy; <a href="http://openstreetmap.org">OpenStreetMap</a> Contributors';
		mapLayer = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: attribution, maxZoom: 18 });
		mapLayer.addTo(this.map);
		
		mqtt = new Paho.MQTT.Client(serverHostname, serverPort, 'WebClient');
		mqtt.onMessageArrived = this.onMessageArrived;
		mqtt.onConnectionLost = this.onConnectionLost
	};
	
	this.connect = function(){
		loginUser = $("#loginUser").val().trim();
		loginPass = $("#loginPass").val().trim();
		
		mqtt.connect({
			timeout: 5,
			cleanSession: true,
			useSSL: true,
			userName: loginUser,
			password: loginPass,
			onSuccess: this.onConnect,
			onFailure: this.onFailure
		});
	};
	
	this.onMessageArrived = function (msg) {
		console.log(msg.destinationName + ": " + msg.payloadString);
	
		carId  = msg.destinationName.split("/")[1];
		carMsg = JSON.parse(msg.payloadString);
	
		if(cars[carId]==undefined){
			cars[carId] = L.marker([carMsg.lat, carMsg.lon], { icon: carIcon});
			cars[carId].addTo(map)
		} else {
			cars[carId].setLatLng(L.latLng(carMsg.lat, carMsg.lon));
		}
	
		cars[carId].setRotationAngle(Number(carMsg.track));
	};

	this.onConnect = function(){
		mqtt.subscribe('car/+/position', {qos: 1});
		$("#connStatus").css('color', 'green');
		$("#map").show();
		$("#loginDialog").hide();
	};
	
	this.onFailure = function(response){
		$("#connStatus").css('color', 'darkred');
		$("#map").hide();
		$("#loginDialog").show();
	};
	
	this.onConnectionLost = function (){
		$("#connStatus").css('color', 'darkred');
		$("#map").hide();
		$("#loginDialog").show();
	};
	
}

carmonitor = new CarMonitor(serverHostname, serverPort, mapStart);
carmonitor.start();