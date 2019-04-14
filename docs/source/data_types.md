# Data Types

The Runway Model SDK provides several data types that can be used to pass values to and from runway models and the applications that control them. The data types currently supported by the SDK are `number`, `text`, `image`, `array`, `vector`, `category`, `file`, and `any`, an extensible data type. These data types are primarily used anywhere in you use the Runway module, however they are most frequently used in two places:

* The `options` parameter in the `@runway.setup()` decorator
* The `input` and `output` parameters in `@runway.command()` decorator

```eval_rst
.. note::
    This is example code for demonstration purposes only. It will not run, as the ``your_code`` import is not a real python module.
```

```python
import runway
from runway.data_types import category, vector, image
from your_code import model

options = {"network_size": category(choices=[64, 128, 256, 512], default=256)}
@runway.setup(options=options)
def setup(opts):
    return model(network_size=opts["network_size"])


sample_inputs= {
    "z": vector(length=512),
    "category": category(choices=["day", "night"])
}

sample_outputs = {
    "image": image(width=1024, height=1024)
}

@runway.command("sample", inputs=sample_inputs, outputs=sample_outputs)
def sample(model, inputs):
    img = model.sample(z=inputs["z"], category=inputs["category"])
    # `img` can be a PIL or numpy image. It will be encoded as a base64 URI
    # string automatically by @runway.command().
    return { "image": img }

if __name__ == "__main__":
    runway.run()
```

## Reference

```eval_rst
.. automodule:: runway.data_types
    :members:

```