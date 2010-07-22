file = open('manyobjects.json', 'w')
file.write('[\n')

object1 = '''    {
        "model": "testapp.testmodel1",
        "pk": %s,
        "fields": {
            "name": "test object 1-%s",
            "owner": 2
        }
    },
'''
for i in range(1, 241):
    file.write(object1 % (i, i))


object2 = '''    {
        "model": "testapp.testmodel2",
        "pk": %s,
        "fields": {
            "name": "test object 2-%s"
        }
    },
'''
file.write(object2 % (1, 1))

droplet = '''    {
        "model": "geyser.droplet",
        "pk": %s,
        "fields": {
            "publishable_type": ["testapp", "testmodel1"],
            "publishable_id": %s,
            "publication_type": ["testapp", "testmodel2"],
            "publication_id": 1,
            "published_by": 2
        }
    }'''
for i in range(1, 240):
    file.write((droplet % (i, i)) + ',\n')
i = 240
file.write((droplet % (i, i)) + '\n')

file.write(']')
file.close()