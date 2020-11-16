def generateErrors(messages):
        payload = {}
        payload['errors'] = messages
        return payload

def generateMessage(msg):
    return {'msg': msg}
