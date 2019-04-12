import runway
from runway.data_types import array, text

@runway.setup(options={ "seed_sentences": array(item_type=text, min_length=5) })
def setup(opts):
    for i in range(5):
        print("Sentence {} is \"{}\"".format(i+1, opts["seed_sentences"][i]))

runway.run()

# curl -H "content-type: application/json" -d '{"seed_sentences": ["the", "sly", "fox", "is", "sly"]}' http://localhost:8000/setup