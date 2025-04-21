'''

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''


class Command:
    
    def __repr__(self):
        return f'<{self.__class__.__name__}>'
    
    def __str__(self):
        return f'{self.__class__.__name__} Command'