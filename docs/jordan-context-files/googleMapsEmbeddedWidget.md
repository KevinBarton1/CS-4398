The following is an example API call URL that loads the Maps Embed API:
https://www.google.com/maps/embed/v1/MAP_MODE?key=YOUR_API_KEY&PARAMETERS

- apikey in .env file
- Map_mode=view
- maptype=roadmap

IFrame example:
<iframe
  width="450"
  height="250"
  frameborder="0" style="border:0"
  referrerpolicy="strict-origin-when-cross-origin"
  src="https://www.google.com/maps/embed/v1/MAP_MODE?key=YOUR_API_KEY&PARAMETERS"
  >
</iframe>