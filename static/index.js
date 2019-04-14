const accessToken = '';

var mymap = L.map('mapid').setView([1.391667, 103.894444], 13);

L.tileLayer(`https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=${accessToken}`, {
  attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
  maxZoom: 18,
  id: 'mapbox.streets',
  accessToken: accessToken
}).addTo(mymap);

var allocations = [{"lng": 103.8172268, "lat": 1.4122635730000002, "frc_supply": 1.0}, {"lng": 103.8586869, "lat": 1.380619209, "frc_supply": 2.0}, {"lng": 103.8793108, "lat": 1.354403108, "frc_supply": 3.0}, {"lng": 103.8354594, "lat": 1.443289319, "frc_supply": 3.0}, {"lng": 103.8919837, "lat": 1.4172600519999998, "frc_supply": 1.0}, {"lng": 103.90055809999998, "lat": 1.3905906419999998, "frc_supply": 2.0}, {"lng": 103.8116929, "lat": 1.453950487, "frc_supply": 1.0}, {"lng": 103.8259146, "lat": 1.386157459, "frc_supply": 2.0}]

allocations.forEach(a => {
  var marker = L.marker([a.lat, a.lng]).addTo(mymap);
  // marker.bindPopup(a.frc_supply);
});

function readTextFile(file, callback) {
  var rawFile = new XMLHttpRequest();
  rawFile.overrideMimeType("application/json");
  rawFile.open("GET", file, true);
  rawFile.onreadystatechange = function() {
      if (rawFile.readyState === 4 && rawFile.status == "200") {
          callback(rawFile.responseText);
      }
  }
  rawFile.send(null);
}

// readTextFile("/../allocation.json", function(text){
//   var data = JSON.parse(text);
//   console.log(data);
// });
