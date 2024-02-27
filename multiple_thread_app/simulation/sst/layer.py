class Layer:
    def __init__(self, id_=0):
        self.id = id_
        self.nodes = []


    def number_of_nodes(self):
        return len(self.nodes)


    def number_of_discrete_nodes(self):
        nodes = [n for n in self.nodes if n.is_discrete()]
        return len(nodes)


    def reset(self):
        for n in self.nodes:
            n.reset_fsm()


    def report_uios(self):
        uios = []
        for n in self.nodes:
            uio_pattern = n.report_uio()
            if uio_pattern is not None:
                uios.append(uio_pattern)
        return uios


    def __str__(self):
        info = ['Layer: ' + str(self.id)]
        for n in self.nodes:
            info.append(str(n))
        info.append('')
        return '\n'.join(info)
            
        
