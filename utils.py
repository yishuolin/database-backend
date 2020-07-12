import random
def genre_selection(atmos):
    switcher={
        'jogging': 'edm',
        'working': 'focus',
        'party': 'techno',
        'workout': 'lo-fi',
        'dinner': 'dinner jazz',
        'morning': 'country pop',
        'chill': 'chill guitar',
        'house':'house'
    }
    return switcher.get(atmos, 'Invalid')

def id_generator():
    return str(random.random())

