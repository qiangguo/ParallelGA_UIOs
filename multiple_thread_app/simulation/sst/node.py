class Node:
    def __init__(self, layer_id, id_=0):
        self.id = id_
        self.layer_id = layer_id
        self.fsm_copies = []
        self.input_labels = []
        self.output_labels = []
        self.parent = None
        self.children = []
        self.traces = []
        self.sep = '.'


    def trace_splitting(self):
        for fsm in self.fsm_copies:
            if fsm.current_state.id != -1:
                self.traces.append(str(fsm.init_state)+' -> ' +
                                   str(fsm.current_state))
            else:
                self.traces.append(str(fsm.init_state)+' -> ERR')


    def splitable(self):
        if self.is_dummy_node():
            return False

        if self.is_discrete():
            return False

        if self.is_stuck_node():
            return False

        return True


    def is_discrete(self):
        if len(self.fsm_copies) != 1:
            return False

        #  If we want to include Dummy Node as UIO, we should
        #  comment this out. In benchmark example (Model I),
        #  only s2 has no definition to the input 'c'. This can
        #  make 'c' distinguishing s2 from others since if we
        #  can use 'c'/None as a broader way to verify s2.

        #if self.is_dummy_node():
        #    return False

        return True


    def is_dummy_node(self):
        if len(self.fsm_copies) == 0:
            return True

        if self.fsm_copies[0].current_state.id == -1:
            return True

        return False


    def is_stuck_node(self):
        s = None
        count = 1
        for m in self.fsm_copies:
            if s is None:
                s = m.current_state
            else:
                if m.current_state.id == s.id:
                    count = count + 1
                s = m.current_state
        return len(self.fsm_copies) == count
                

    def reset_fsm(self):
        for m in self.fsm_copies:
            m.reset()


    def report_uio(self):
        if not self.is_discrete():
            return None

        uio = (self.fsm_copies[0].init_state.id,
               ''.join(self.input_labels),
               ''.join(self.output_labels))

        return uio


    def __str__(self):
        info = ['Layer ' + str(self.layer_id) + ' : Node: ' + str(self.id),
                'Inputs:  ' + self.sep.join(self.input_labels),
                'Outputs:  ' + self.sep.join(self.output_labels),
                '- FSM Copies -']

        info.extend(['  M(From -> To): ' + trace for trace in self.traces])

        info.append('')

        return '\n'.join(info)
