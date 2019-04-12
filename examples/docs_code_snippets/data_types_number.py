import runway
from runway.data_types import number

@runway.setup(options={ "number_of_samples": number })
def setup(opts):
    print("The number of samples is {}".format(opts["number_of_samples"]))

runway.run()

# curl -H "content-type: application/json" -d '{"number_of_samples": 5}' http://localhost:8000/setup