import runway
from runway.data_types import category

# if no default value is specified, the first element in the choices
# list will be used
cat = category(choices=["rgb", "bgr", "rgba", "bgra"], default="rgba")
@runway.setup(options={ "pixel_order": cat })
def setup(opts):
    print("The selected pixel order is {}".format(opts["pixel_order"]))

runway.run()

# curl -H "content-type: application/json" -d '{"pixel_order": "bgr"}' http://localhost:9000/setup