const accessToken = '';

$(document).ready(function() {
  var mymap = L.map('mapid').setView([1.391667, 103.894444], 13);

  L.tileLayer(`https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=${accessToken}`, {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    maxZoom: 18,
    id: 'mapbox.streets',
    accessToken: accessToken
  }).addTo(mymap);

  $.getJSON(`http://localhost:5000/solution`, function(allocations) {
    allocations.forEach(a => {
      var marker = L.marker([a.lat, a.lng]).addTo(mymap);
      marker.bindPopup(`${a.frc_supply} car(s)`);
    });
  })
})
