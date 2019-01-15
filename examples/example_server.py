from runway import RunwayModel


model = RunwayModel()


@model.command('lower2upper', inputs={'lowercase': 'text'}, outputs={'results': [{'uppercase': 'text'}]})
def infer(model, input):
    return {'results': [{'uppercase': input['lowercase'].upper()}]}


@model.command('upper2lower', inputs={'uppercase': 'text'}, outputs={'results': [{'lowercase': 'text'}]})
def infer(model, input):
    return {'results': [{'lowercase': input['uppercase'].lower()}]}


if __name__ == '__main__':
    model.run()
