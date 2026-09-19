# vendor

`index.html` loads three.js from a CDN by default. If venue Wi-Fi is
flaky (per the brief's known-unknowns list), download the matching
`three.module.js` + `webxr/VRButton.js` / `ARButton.js` build here and
switch the `<script type="importmap">` in `index.html` to point at these
local files instead.
