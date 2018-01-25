var cars;
var map;

var carIcon = L.icon({
    iconUrl: '/style/arrow.png',
    iconSize: [32, 32],
	iconAnchor: [16, 16],
    popupAnchor: [16, 16]
});

$(document).ready(function(){
	setupLeafletMap();
	setupLoginDialog();
});

function setupLeafletMap() {
	map = L.map('map', {
		center: mapStart,
		zoom: 14
	});

	attribution = '&copy; <a href="http://openstreetmap.org">OpenStreetMap</a> Contributors';
	mapLayer = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: attribution, maxZoom: 18 });
	mapLayer.addTo(map);
}

function setupLoginDialog() {
	$("#loginButton").click(function(){
		loginUser = $("#loginUser").val().trim();
		loginPass = $("#loginPass").val().trim();
		setupServerConnection(loginUser, loginPass);
		$("#serverStatus").html('Verbinde...');
	});
}

function setupServerConnection(loginUser, loginPass) {
	cars = [];

	mqtt = new Paho.MQTT.Client(serverHostname, serverPort, 'WebClient');
	mqtt.onMessageArrived = onMessageArrived;
	mqtt.onConnectionLost = onConnectionLost
	
	mqtt.connect({
		timeout: 5,
		cleanSession: true,
		useSSL: true,
		userName: loginUser,
		password: loginPass,
		onSuccess: onConnect,
		onFailure: onFailure
	});
}

function onConnect() {
	mqtt.subscribe('car/+/position', {qos: 1});
	$("#serverStatus").html(serverHostname);
	$("#loginDialog").hide();
}

function onConnectionLost(){
	$("#serverStatus").html('Verbindung unerwartet getrennt');
	$("#loginDialog").show();
}

function onFailure(response) {
	$("#serverStatus").html('Verbindungsfehler ' + response.errorMessage);
	$("#loginDialog").show();
}

function onMessageArrived(msg) {
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
	//cars[carId].bindPopup('<strong>'+carId+'</strong><br>Lat: ' + carMsg.lat + ', Lon: ' + carMsg.lon)
	
	$("#carInfo").html(carId + ' | Geschwindigkeit: ' + Math.round(carMsg.speed * 3.6) + ' km/h | Höhe: ' + Math.round(carMsg.alt) + ' m | Kurs ' + Math.round(carMsg.track) + '° | Steigrate ' + Math.round(carMsg.climb) + ' m/s');
};


