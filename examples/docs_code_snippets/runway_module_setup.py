import runway
from runway.data_types import category
from your_code import model

# Descriptions are used to document each data type; Their values appear in the app as
# tooltips. Writing detailed descriptions for each model option goes a long way towards
# helping users learn how to interact with your model. Write descriptions as full sentences.
network_size_description = "The size of the network. A larger number will result in" \
                           "better accuracy at the expense of increased latency."
options = {
  "network_size": category(choices=[64, 128, 256, 512], default=256, description=network_size_description)
}
@runway.setup(options=options)
def setup(opts):
    print("Setup ran, and the network size is {}".format(opts["network_size"]))
    return model(network_size=opts["network_size"])
