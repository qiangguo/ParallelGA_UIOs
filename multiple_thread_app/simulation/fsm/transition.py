class Transition:
    def __init__(self,
                 id_,
                 start_state,
                 end_state,
                 i,
                 o,
                 token=''):
        self.id = id_
        self.start_state = start_state
        self.end_state = end_state
        self.input = i
        self.output = o
        self.token = token.strip()


    def __str__(self):
        info = ('t'+str(self.id) + ': ' +
                's' + str(self.start_state.id) +
                " - (" + self.input + "/" + self.output + ") -> " +
                's' + str(self.end_state.id))
        
        if self.token == '':
            return info
    
        return info + '  |= ' + self.token