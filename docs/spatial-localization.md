# Automatic spatial localization

## Implemented path

1. Pair Quest with a desktop cooking session and start monitoring. Grant camera and spatial-data permissions; no pointing or object placement is required.
2. Quest captures an image and a 17-by-13 grid of environment-depth hits using the capture camera pose. Coordinates are converted to the image's top-left convention before upload.
3. The existing vision call returns equipment labels and normalized bounding boxes. Backend validation rejects malformed, low-confidence and out-of-frame detections. The model is never asked to invent world coordinates.
4. Quest uses three nearby, consistent measured points inside the box's central region to estimate a surface position. Missing/discontinuous depth means no label.
5. Two distinct observations at nearby positions confirm a label. Labels sit above measured surfaces, face the viewer, and expire when stale. Pausing, disconnecting or finishing clears them. Equipment uses text labels; only the summoned chef uses the textured cube.

## Limits

This is sampled localization of mostly stationary equipment, not continuous tracking of moving utensils. Small objects may not cover enough grid samples. Similar nearby objects can be confused; labels are not persistent object identities. Depth and RGB are captured during the same update but are not guaranteed hardware-synchronized. Camera orientation and measured-depth alignment require device calibration checks.

Detections use the existing, still-unverified vision-provider adapter. The code path is implemented, but no live CV or Quest localization result is claimed. Results older than 15 seconds are discarded; slow providers may therefore produce no labels. Confident model output can still be wrong, and depth alone cannot establish object identity.

## Checks

Backend tests validate box bounds, malformed data, confidence, injection-like labels and integration with step assistance. In Unity, **Ramsey > Validate Spatial Geometry** checks missing depth, insufficient samples, consistent surfaces, depth edges, invalid boxes, pixel filtering and the portrait shader. Seven checks passed in the Editor; physical camera/depth tests remain outstanding.

Device acceptance: identify a stationary board/bowl/press without pointing; turn your head and verify world alignment; obscure/move the object and verify stale labels disappear; deny depth permission and verify no fabricated positions; pause monitoring and verify labels clear. Check processing latency before claiming responsive tracking.

References: [Meta camera API](https://developers.meta.com/horizon/documentation/unity/unity-pca-documentation/) and the installed SDK's `PassthroughCameraAccess`/`EnvironmentRaycastManager` source. [Build instructions](build-plan.md).
