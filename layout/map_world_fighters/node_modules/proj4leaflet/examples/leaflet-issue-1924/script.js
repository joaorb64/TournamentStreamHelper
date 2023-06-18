var crs = new L.Proj.CRS.TMS(
	    'EPSG:3948',
	    '+proj=lcc +lat_1=47.25 +lat_2=48.75 +lat_0=48 +lon_0=3 +x_0=1700000 +y_0=7200000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs',
	    [0, 0, 1e10, 1e10],
	    { resolutions: [53.97500000000001,6.987500000000004,16.192500000000003,8.096250000000001,6.746875000000001,4.048125000000001,2.6987500000000004,2.0240625000000003,1.3493750000000002,0.9445625000000001,0.6746875000000001,0.5397500000000001,0.4048125000000001,0.26987500000000003,0.13493750000000002] }
	),
	map = L.map('map', {
		crs: crs,
		continuousWorld: true,
		worldCopyJump: false,
		zoomControl: true
	});

new L.TileLayer('http://i{s}.maps.daum-img.net/map/image/G03/i/1.20/L{z}/{y}/{x}.png', {
	maxZoom: 14,
	minZoom: 0,
	zoomReverse: true,
	subdomains: '0123',
	continuousWorld: true,
	attribution: 'ⓒ 2012 Daum',
	tms: true
}).addTo(map);

map.setView([38.0, 127.0], 0);
