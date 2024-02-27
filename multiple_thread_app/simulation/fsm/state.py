class State:
    def __init__(self, id_=-1, icon='s', token=''):
        """
        If id_ == -1, it implies it is an error state.
        """
        self.id = id_
        self.out_trans = ()
        self.in_trans = ()
        self.icon = icon
        self.token = token.strip()


    def add_out_transition(self, tr):
        self.out_trans = list(self.out_trans)
        self.out_trans.append(tr)
        self.out_trans = tuple(self.out_trans)


    def add_in_transition(self, tr):
        self.in_trans = list(self.in_trans)
        self.in_trans.append(tr)
        self.in_trans = tuple(self.in_trans)


    def get_in_degree(self):
        return len(self.in_trans)


    def get_out_degree(self):
        return len(self.out_trans)


    def __str__(self):
        if self.token != '':
            return self.icon + str(self.id) + '  |=> ' + self.token
        return self.icon + str(self.id)
