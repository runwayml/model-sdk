import runway
from runway.data_types import category
from your_code import model

options = {"network_size": category(choices=[64, 128, 256, 512], default=256)}
@runway.setup(options=options)
def setup(opts):
    print("Setup ran, and the network size is {}".format(opts["network_size"]))
    return model(network_size=opts["network_size"])