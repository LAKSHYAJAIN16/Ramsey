# Desktop companion

Served at `/app/` by the Python backend. Users sign in, select recipes, and set up the session the Quest will join. The desktop is the selection/control surface; the headset is the intended cooking surface.

Start with [index.html](index.html), then [JavaScript modules](js/README.md) and [styles](css/README.md). Firebase sign-in and live recipe acquisition require configuration. Do not treat a static page load as a verified signed-in session.

Run the backend from the [root instructions](../README.md). There is no separate frontend build step. JavaScript syntax is checked in CI; browser and device acceptance is described in [the demo guide](../docs/judging.md).
