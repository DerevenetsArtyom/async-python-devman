# Buses on the map of Moscow

Web application shows the movement of buses on the map of Moscow.

<img src="screenshots/buses.gif">

## How to launch

- Download the code
- Open the index.html file in your browser


# Settings

At the bottom right of the page, you can enable logging debug mode and specify a non-standard web socket address.

<img src="screenshots/settings.png">

The settings are saved in the Local Storage of the browser and do not disappear after the page is refreshed. To reset the settings, remove the keys from the Local Storage using Chrome Dev Tools -> Application tab -> Local Storage.

If something does not work as expected, start by enabling debugging.

## Data format

Frontend expects to receive JSON message with a list of buses from server:

```js
{
  "msgType": "Buses",
  "buses": [
    {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"},
    {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670к"}
  ]
}
```

Those buses that are not on the `buses` list of the last message from the server will be removed from the map.

The frontend tracks the movement of the user on the map and sends to the server new coordinates of the window:

```js
{
  "msgType": "newBounds",
  "data": {
    "east_lng": 37.65563964843751,
    "north_lat": 55.77367652953477,
    "south_lat": 55.72628839374007,
    "west_lng": 37.54440307617188
  }
}
```



## Used libraries

- [Leaflet](https://leafletjs.com/) - Drawing a map
- [loglevel](https://www.npmjs.com/package/loglevel) for logging


# The goals of the project

The code is written for training purposes and is a lesson in a course on Python and web development at [Devman](https://dvmn.org).
