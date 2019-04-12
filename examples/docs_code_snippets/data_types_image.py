import runway
from runway.data_types import image

inputs = {"image": image(width=512, height=512)}
outputs = {"image": image(width=512, height=512)}
@runway.command("style_transfer", inputs=inputs, outputs=outputs)
def style_transfer(result_of_setup, args):
    # perform some transformation to the image, and then return it as a
    # PIL image or numpy array
    img = do_style_transfer(args["image"])
    return { "image": img }

runway.run()
# curl -H "content-type: application/json" -d '{ "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgA..." }' http://localhost:8000/batch_process