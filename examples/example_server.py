import runway
import time
from runway.data_types import text

@runway.setup(options={'suffix': text})
def setup(options):
    return options['suffix']


@runway.command('lower2upper', inputs={'input': text}, outputs={'output': text})
def lower2upper(suffix, inputs):
    out = inputs['input'].upper() + suffix
    ret = ''
    for c in out:
        ret += c
        yield ret, len(ret)/len(out)
        time.sleep(1)
    yield ret


if __name__ == '__main__':
    runway.run()
