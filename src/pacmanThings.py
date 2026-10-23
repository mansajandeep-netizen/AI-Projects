'''Things that live in the PacMan World (Task 3).'''
from src.thingClass import Thing


class Food(Thing):
    '''A Fixed Food Dot. Eating it doubles the agent's performance (Task 5).'''
    def __init__(self, location=None):
        self.location = location

    def __repr__(self):
        return f'<Food {self.location}>'


class Ghost(Thing):
    '''A hidden Ghost with a Power. The agent does not know where ghosts are;
    it only notices one when it steps into the ghost's cell (Task 6).'''
    def __init__(self, power, location=None):
        self.power = power
        self.location = location
        self.alive = True

    def __repr__(self):
        return f'<Ghost {self.location} power={self.power}>'
