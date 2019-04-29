# Changelog

## v0.0.70

- Add `modelSDKVersion` to manifest at `GET /`.
- Add `millisRunning` to manifest at `GET /`.
- Add `millisSinceLastCommand` to manifest at `GET /`.
- Add `GPU` to manifest at `GET /` so that a model's GPU accessibility can be determined at runtime.
- Add undocumented `millis_running()` and `millis_since_last_command()` to `RunwayModel`.
- Add `default` parameter to `vector` data type.
- Add `RW_NO_SERVE` environment variable and `no_serve` keyword argument to `runway.run()`. These settings prevent `runway.run()` from starting the Flask server so that mock HTTP requests can be made via `app.test_client()`. See [Testing Flask Applications](http://flask.pocoo.org/docs/1.0/testing/) for more details.
- Add model tests in [`tests/test_model.py`](tests/test_model.py)
- Minor change to `docs/` so that JavaScript HTTP -> HTTPS redirect only occurs when the protocol is actually `http:`.
