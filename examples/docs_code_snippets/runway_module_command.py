import runway
from runway.data_types import category, vector, image
from your_code import model, base64EncodeImage

@runway.setup
def setup():
    return model()

sample_inputs= {
    "z": vector(length=512),
    "category": category(choices="day", "night")
}

sample_outputs = {
    "image": image(width=1024, height=1024)
}

@runway.command("sample", inputs=sample_inputs, outputs=sample_outputs)
def sample(model, inputs):
    # The parameters passed to a function decorated by @runway.command() are:
    #   1. The return value of a function wrapped by @runway.setup(), usually a model
    #   2. The inputs sent with the HTTP request to the /<command_name> endpoint,
    #      as defined by the inputs keyword argument delivered to @runway.command().
    img = model.sample(z=inputs["z"], category=inputs["category"])
    return { "image": base64EncodeImage(img) }

