import random
def genre_selection(atmos):
    switcher={
        'jogging': 'edm',
        'working': 'focus',
        'party': 'panamanian rock',
        'workout': 'electronic rock',
        'dinner': 'classic soul',
        'morning': 'bossa nova'
    }
    return switcher.get(atmos, 'Invalid')

def id_generator():
    return str(random.random())

