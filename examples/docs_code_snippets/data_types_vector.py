import runway
from runway.data_types import vector, number
import numpy as np

inputs={"length": number(min=1)}
outputs={"vector": vector(length=512)}
@runway.command("random_sample", inputs=inputs, outputs=outputs)
def random_sample(result_of_setup, args):
    # TODO: Come back, I think there is a bug here...
    # we should be returning a serialized version of the data, not a deserialized version...
    vec = vector(length=args["length"])
    rand = np.random.random_sample(args["length"])
    return { "vector": vec.deserialize(rand) }

runway.run()

# curl -H "content-type: application/json" -d '{"length": 128}' http://localhost:9000/random_sample