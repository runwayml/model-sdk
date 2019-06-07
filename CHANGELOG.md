# Changelog

## v0.0.75

- Use PNG as default serialization format for images.

## v0.0.74

- Use PNG, instead of JPEG, as default serialization format for images.

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
