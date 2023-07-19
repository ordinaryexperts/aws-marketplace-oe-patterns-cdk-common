import json

def print_resource(template, type):
  resource = template.find_resources(type)
  print('******')
  print(json.dumps(resource, indent=4, sort_keys=True))
  print('******')
