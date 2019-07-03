import runway
from runway.data_types import category, vector, image
from your_code import model

@runway.setup
def setup():
    return model()

sample_inputs= {
    "z": vector(length=512, description="The seed used to generate an output image."),
    "category": category(choices=["day", "night"])
}

sample_outputs = {
    "image": image(width=1024, height=1024)
}

# Descriptions are used to document each data type and `@runway.command()`; Their values appear
# in the app as tooltips. Writing detailed descriptions for each model option goes a long way
# towards helping users learn how to interact with your model. Write descriptions as full
# sentences.
sample_description = "Generate a new image based on a z-vector and an output style: Day or night."
@runway.command("sample",
                inputs=sample_inputs,
                outputs=sample_outputs,
                description=sample_description)
def sample(model, inputs):
    # The parameters passed to a function decorated by @runway.command() are:
    #   1. The return value of a function wrapped by @runway.setup(), usually a model.
    #   2. The inputs sent with the HTTP request to the /<command_name> endpoint,
    #      as defined by the inputs keyword argument delivered to @runway.command().
    img = model.sample(z=inputs["z"], category=inputs["category"])
    # `img` can be a PIL or numpy image. It will be encoded as a base64 URI string
    # automatically by @runway.command().
    return { "image": img }
