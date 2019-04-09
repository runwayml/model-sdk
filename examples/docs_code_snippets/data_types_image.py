import runway
from runway.data_types import image

inputs = {"image": image(width=512, height=512)}
outputs = {"image": image(width=512, height=512)}
@runway.command("style_transfer", inputs=inputs, outputs=outputs)
def style_transfer(result_of_setup, args):
    # perform some transformation to the image, and then return it as a base64 string
    base64String = do_style_transfer(args["image"])
    return { "image": base64String }

runway.run()
# curl -H "content-type: application/json" -d '{"folder": "test"}' http://localhost:8000/batch_process