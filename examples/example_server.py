from runway import RunwayServer


server = RunwayServer('Test Model')


@server.command('example-command', inputs={'lowercase': 'text'}, outputs={'results': {'arrayOf': {'uppercase': 'text'}}})
def infer(input):
    return {'results': [{'uppercase': input['lowercase'].upper()}]}


if __name__ == '__main__':
    server.run()
