import runway
from runway.data_types import text, number, array

@runway.setup(options={'seed': number(default=0, max=5, step=1)})
def setup(options):
    print(options['seed'])


@runway.command('lower2upper', inputs=[array(text)], outputs=[array(text)])
def lower2upper(model, texts):
    return [text.upper() for text in texts]


@runway.command('upper2lower', inputs=[text], outputs=[text])
def upper2lower(model, text):
    return text.lower()


if __name__ == '__main__':
    runway.run()
