import runway
from runway.data_types import text

@runway.setup(options={'suffix': text})
def setup(options):
    return options['suffix']

import time

@runway.command('lower2upper', inputs={'input': text}, outputs={'output': text})
def lower2upper(suffix, inputs):
    result = inputs['input'].upper() + suffix
    ret = ''
    for i in range(len(result)):
        ret += result[i]
        yield ret
        time.sleep(1)
    # return {'output': }


if __name__ == '__main__':
    runway.run()
