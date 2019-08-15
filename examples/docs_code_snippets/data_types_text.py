import runway
from runway.data_types import text

@runway.setup(options={ "flavor": text(default="vanilla") })
def setup(opts):
    print("The selected flavor is {}".format(opts["flavor"]))

runway.run()

# curl -H "content-type: application/json" -d '{"flavor": "chocolate"}' http://localhost:9000/setup