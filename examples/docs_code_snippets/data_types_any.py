import yaml
import runway
from runway.data_types import any
# from your_code import model

# an example of passing your own yaml configuration using an "any" data_type and PyYAML
@runway.setup(options={ "configuration": any() })
def setup(opts):
    config = yaml.load(opts["configuration"])
    print(config)
    # return model(config)

runway.run()

# curl -H "content-type: application/json" -d '{"configuration": "# A list of tasty fruits\nfruits:\n  - Apple\n  - Orange\n  - Strawberry\n  - Mango"}' http://localhost:9000/setup
