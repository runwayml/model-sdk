import runway
from runway.data_types import text

@runway.setup(options={'suffix': text})
def setup(options):
    return options['suffix']


@runway.command('lower2upper', inputs={'input': text}, outputs={'output': text})
def lower2upper(suffix, inputs):
    return {'output': inputs['input'].upper() + suffix}


if __name__ == '__main__':
    runway.run()
