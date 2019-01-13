from runway import RunwayModel


model = RunwayModel()


@model.command('example-command', inputs={'lowercase': 'text'}, outputs={'results': [{'uppercase': 'text'}]})
def infer(model, input):
    print(model)
    return {'results': [{'uppercase': input['lowercase'].upper()}]}


if __name__ == '__main__':
    model.run()
