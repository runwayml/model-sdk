import runway
from runway.data_types import file, category

inputs = {"folder": file(is_folder=True)}
outputs = {"result": category(choices=["success", "failure"])}
@runway.command("batch_process", inputs=inputs, outputs=outputs)
def batch_process(result_of_setup, args):
    result = True # do_something_with(args["folder"])
    return { "result": "success" if result else "failure" }

runway.run()

# curl -H "content-type: application/json" -d '{"folder": "test"}' http://localhost:8000/batch_process