import random
def genre_selection(atmos):
    switcher={
        'jogging': 'folk-pop',
        'working': 'focus',
        'party': 'edm',
        'workout': 'lo-fi',
        'dinner': 'dinner jazz',
        'morning': 'country pop',
        'chill': 'chill guitar'
    }
    return switcher.get(atmos, 'Invalid')

def id_generator():
    return str(random.random())