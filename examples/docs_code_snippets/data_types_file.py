import runway
from runway.data_types import file, category

inputs = {"directory": file(is_directory=True)}
outputs = {"result": category(choices=["success", "failure"])}
@runway.command("batch_process", inputs=inputs, outputs=outputs)
def batch_process(result_of_setup, args):
    result = True # do_something_with(args["directory"])
    return { "result": "success" if result else "failure" }

runway.run()

# curl -H "content-type: application/json" -d '{"directory": "test"}' http://localhost:8000/batch_process