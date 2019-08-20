# Changelog

The Runway Model SDK follows [semantic versioning](https://semver.org/). Be aware that breaking changes may be introduced in minor version updates until a stable 1.0.0 release occurs per [SemVer spec #4](https://semver.org/#spec-item-4).

> 4. Major version zero (0.y.z) is for initial development. Anything may change at any time. The public API should not be considered stable.

Until version 1.0.0, expect that minor version changes may introduce breaking changes. We will take care not to introduce new behavior, features, or breaking changes in patch releases. If you require stability and reproducible behavior you *may* pin to a version or version range of the model SDK like `runway-python>=0.2.0` or `runway-python>=0.2,<0.3`.

## v.0.4.1

- Set default port to 9000.

## v.0.4.0

- Add `image_landmarks` data type.

## v.0.3.2

- Make segmentation serialize as a 3-channel color map when used as an output field, instead of a 1-channel label map.

## v.0.3.1

- Remove default values for `min`, `max`, and `step` parameters of `number` data type.
- Rename `type` field of `image_point.to_dict()` response from `point` to `image_point`.

## v0.3.0

- Add `image_point` data type.
- Add `image_bounding_box` data type.

## v0.2.0

- Add `boolean` data type.

## v0.1.0

- Add `segmentation` data type.
- Begin strict [semantic versioning](https://semver.org/).

## v0.0.75

- Use PNG as default serialization format for images.

## v0.0.74

- Remove `name` keyword argument from all `runway.data_types`. [#13](https://github.com/runwayml/model-sdk/issues/13)
- Add `description` keyword argument to all `runway.data_types` and `runway.command()`. [#12](https://github.com/runwayml/model-sdk/issues/12)
- Create abstract `runway.data_types.BaseType` class that defines a common interface for all `runway.data_types`.

## v0.0.73

- Add support for all remote filetypes over HTTP (we are currently only supporting tarballs)
- Add extneison argument to the file type and enforce that during deserialization
- Rename is_folder to is_directory

## v0.0.70

- Move `/` meta endpoint to `/meta` and specify `GET` as the only allowed method (its still available via `/` for backwards compatibility).
- `/healthcheck` endpoint now returns JSON (e.g. `{ "status": "RUNNING" }`)
- Limit `/healthcheck` to only allow HTTP methods.
- Add `modelSDKVersion` to manifest at `GET /meta`.
- Add `millisRunning` to manifest at `GET /meta`.
- Add `millisSinceLastCommand` to manifest at `GET /meta`.
- Add `GPU` to manifest at `GET /meta` so that a model's GPU accessibility can be determined at runtime.
- Add undocumented `millis_running()` and `millis_since_last_command()` to `RunwayModel`.
- Add `default` parameter to `vector` data type.
- Model server now wraps common server error codes in JSON responses (e.g. 401, 403, 404, 405, 500).
- Model server now sniffs the body of `POST` for JSON even if `content-type: application/json` is not sent in the request header. [#1](https://github.com/runwayml/model-sdk/issues/1)
- Model server now returns `content-type: application/json`. [#6](https://github.com/runwayml/model-sdk/issues/6)
- Add `RW_NO_SERVE` environment variable and `no_serve` keyword argument to `runway.run()`. These settings prevent `runway.run()` from starting the Flask server so that mock HTTP requests can be made via `app.test_client()`. See [Testing Flask Applications](http://flask.pocoo.org/docs/1.0/testing/) for more details.
- Add model tests in [`tests/test_model.py`](tests/test_model.py)
- Minor change to `docs/` so that JavaScript HTTP -> HTTPS redirect only occurs when the protocol is actually `http:`.
