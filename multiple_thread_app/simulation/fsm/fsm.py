from . import state
from . import transition

import copy
import random
import sys
import os
from datetime import datetime


class FSM:
    SEP = ':'

    def __init__(self, f_fsm_file=None, parms={}, save_enabled=True):
        self.parms = parms
        self.num_of_states = 0
        self.num_of_transitions = 0
        self.input_set = None
        self.output_set = None
        self.states = []
        self.transitions = []
        self.current_state = None
        self.init_state = None

        if f_fsm_file:
            self.__read_fsm(f_fsm_file)
            self.num_of_transitions = len(self.states)
            self.num_of_transitions = len(self.transitions)
        else:
            self.__generate_random_fsm(save_enabled)
            self.num_of_transitions = len(self.states)
            self.num_of_transitions = len(self.transitions)


    def __read_fsm(self, f_fsm_file):
        with open(f_fsm_file, 'r') as fn:
            for line in fn:
                line = line.strip()
                items = line.split(':')
                items = [item.strip() for item in items]
                
                if items[0].lower() == 'states':
                    self.num_of_states = int(items[1])
                    if len(items) > 2:
                        tokens = items[-1]
                    else:
                        tokens = ''
                    tokens = tokens.split('|')
                    tokens = [t.strip() for t in tokens]
                    self.__create_states(tokens)
                elif items[0].lower() == 'input_set':
                    symbols = items[1].split(',')
                    symbols = [c.strip() for c in symbols]
                    self.input_set = tuple(symbols)
                elif items[0].lower() == 'output_set':
                    symbols = items[1].split(',')
                    symbols = [c.strip() for c in symbols]
                    self.output_set = tuple(symbols)
                elif items[0] == '':
                    continue
                else:
                    self.transitions.append(self.__create_trans(items))
                    self.num_of_transitions += 1
        self.transitions = tuple(self.transitions)


    def __generate_random_fsm(self, save_enabled):
        settings = self.parms['FSM']['FSMDefault']    
        self.num_of_states = settings.get('NumberOfStates', 100)
        self.input_set = tuple(settings.get('InputSet', ('a', 'b', 'c')))
        self.output_set = tuple(settings.get('OutputSet', ('x', 'y')))

        self.__create_states()

        digraph_options = settings['DigraphShapeOptions']
        digraph_sel = settings['DigraphShapeSelection']

        if digraph_options[digraph_sel] == 'complete-random-symmetric':
            self.__complete_random_symmetric(settings, save_enabled)
        elif digraph_options[digraph_sel] == 'complete-random-uniform':
            self.__complete_random_uniform(settings, save_enabled)
        elif digraph_options[digraph_sel] == 'complete-random-normal':
            self.__complete_random_normal(settings, save_enabled)
        elif digraph_options[digraph_sel] == 'partial-random-uniform':
            self.__partial_random_uniform(settings, save_enabled)
        elif digraph_options[digraph_sel] == 'partial-random-normal':
            self.__partial_random_normal(settings, save_enabled)
        else:
            raise TypeError('Not defined FSM shape pattern!')


    def __create_states(self, tokens=[]):
        for i in range(self.num_of_states):
            try:
                t = tokens[i]
            except:
                t = ''
            s = state.State(i, token=t)
            self.states.append(s)
        self.states = tuple(self.states)
        self.set_init_state(0)
        self.set_current_state(0)


    def __create_trans(self, info):
        try:
            tr_id, start_s_id, end_s_id, i, o, t = info
            t = t.strip()
        except:
            tr_id, start_s_id, end_s_id, i, o = info
            t = ''

        tr_id = int(tr_id)
        start_s_id = int(start_s_id)
        end_s_id = int(end_s_id)

        start_s = False
        end_s = False

        for s in self.states:
            if s.id == start_s_id:
                start_s = s
            if s.id == end_s_id:
                end_s = s
            if start_s and end_s:
                break

        
        trx = transition.Transition(tr_id,
                                    start_s,
                                    end_s,
                                    i,
                                    o,
                                    t)
        start_s.add_out_transition(trx)
        end_s.add_in_transition(trx)
        return trx


    def __complete_random_symmetric(self, settings, save_enabled):
        """
        The randomly generated FSM is completely specified with a symmetric
        digraph, i.e., for each state, the in-degree = out-degree = input size
        """
        tr_id = 0
        transitions = []
        for s_start in self.states:
            indexes = list(range(len(self.states)))
            for i in self.input_set:
                while indexes:
                    random.shuffle(indexes)
                    s_end_id = indexes[0]
                    s_end = self.states[s_end_id]

                    if s_end.get_in_degree() < len(self.input_set):
                        pos = random.randint(0, len(self.output_set)-1)
                        o = self.output_set[pos]
                        trx = transition.Transition(tr_id,
                                                    s_start,
                                                    s_end,
                                                    i, o, '')
                        s_start.add_out_transition(trx)
                        s_end.add_in_transition(trx)
                        transitions.append(trx)
                        tr_id = tr_id + 1
                        break
                    else:
                        indexes.remove(s_end_id)

        self.transitions = tuple(transitions)
        if save_enabled:
            self.save_fsm('symmetric', settings)


    def __complete_random_uniform(self, settings, save_enabled):
        """
        The randomly generated FSM is completely specified, i.e., each
        state has full definitions to respond all inputs but, for a transition,
        the ending state is randomly selected following a uniform distribution.
        To ensure the digraph is strongly connected, each state has at least 1
        in-degree.
        """
        tr_id = 0
        transitions = []

        first_run = list(range(len(self.states)))
        state_ids = list(range(len(self.states)))

        for s_start in self.states:            
            for i in self.input_set:
                s_end = None
                #  The following ensures that each state must have at least
                #  in-degree two but not a loop.
                while first_run:
                    s_end_id = random.randint(0, len(first_run)-1)
                    if s_start.id != first_run[s_end_id]:
                        s_end = self.states[first_run[s_end_id]]

                        if s_end.get_in_degree() > 1:
                            first_run.remove(first_run[s_end_id])
                        break
                    else:
                        if len(first_run) == 1:
                            s_end = self.states[first_run[s_end_id]]
                            first_run = []
                            break

                if s_end is None:
                    s_end_id = random.randint(0, len(state_ids)-1)
                    s_end = self.states[state_ids[s_end_id]]

                pos = random.randint(0, len(self.output_set)-1)
                o = self.output_set[pos]
                trx = transition.Transition(tr_id,
                                            s_start,
                                            s_end,
                                            i, o, '')
                s_start.add_out_transition(trx)
                s_end.add_in_transition(trx)
                transitions.append(trx)
                tr_id = tr_id + 1

        self.transitions = tuple(transitions)

        if save_enabled:
            self.save_fsm('complete_uniform', settings)


    def __complete_random_normal(self, settings, save_enabled):
        """
        The randomly generated FSM is completely specified, i.e., each
        state has full definitions to respond all inputs but, for a transition,
        the ending state is randomly selected following a normal distribution.
        This implies that some states have much higher in-degree that others.
        To ensure the digraph is strongly connected, each state has at least 1
        in-degree.
        """
        tr_id = 0
        transitions = []

        first_run = list(range(len(self.states)))
        state_ids = list(range(len(self.states)))

        for s_start in self.states:            
            for i in self.input_set:
                s_end = None
                #  The following ensures that each state must have at least
                #  in-degree two but not a loop.
                while first_run:
                    s_end_id = random.randint(0, len(first_run)-1)
                    if s_start.id != first_run[s_end_id]:
                        s_end = self.states[first_run[s_end_id]]

                        if s_end.get_in_degree() > 1:
                            first_run.remove(first_run[s_end_id])
                        break
                    else:
                        if len(first_run) == 1:
                            s_end = self.states[first_run[s_end_id]]
                            first_run = []
                            break

                if s_end is None:                    
                    #  Determining the ending state's ID following Gaussian
                    #  distribution. If pos runs out of the range, then the
                    #  last state is used.
                    s_end_id = abs(int(random.normalvariate(
                        self.num_of_states//2,
                        self.num_of_states//3)))
                    if s_end_id > self.num_of_states - 1:
                        s_end_id = self.num_of_states // 2
                    s_end = self.states[state_ids[s_end_id]]

                pos = abs(int(random.normalvariate(self.num_of_states//2,
                                                   self.num_of_states/3)))
                
                pos = random.randint(0, len(self.output_set)-1)
                o = self.output_set[pos]
                trx = transition.Transition(tr_id,
                                            s_start,
                                            s_end,
                                            i, o, '')
                s_start.add_out_transition(trx)
                s_end.add_in_transition(trx)
                transitions.append(trx)
                tr_id = tr_id + 1
        self.transitions = tuple(transitions)

        if save_enabled:
            self.save_fsm('complete_gauss', settings)


    def __partial_random_uniform(self, settings, save_enabled, from_=1):
        """
        The randomly generated FSM is partially specified, i.e., each
        state only responds to a subset of the inputs. For a transition,
        the ending state is randomly selected following a uniform distribution.
        To ensure the digraph is strongly connected, each state has at least 1
        in-degree.
        """
        tr_id = 0
        transitions = []

        first_run = list(range(len(self.states)))
        state_ids = list(range(len(self.states)))

        for s_start in self.states:
            inputs = list(self.input_set)
            random.shuffle(inputs)
            inputs = inputs[from_:]
            for i in inputs:
                s_end = None
                #  The following ensures that each state must have at least
                #  in-degree two but not a loop.
                while first_run:
                    s_end_id = random.randint(0, len(first_run)-1)
                    if s_start.id != first_run[s_end_id]:
                        s_end = self.states[first_run[s_end_id]]

                        if s_end.get_in_degree() > 1:
                            first_run.remove(first_run[s_end_id])
                        break
                    else:
                        if len(first_run) == 1:
                            s_end = self.states[first_run[s_end_id]]
                            first_run = []
                            break

                if s_end is None:
                    s_end_id = random.randint(0, len(state_ids)-1)
                    s_end = self.states[state_ids[s_end_id]]

                pos = random.randint(0, len(self.output_set)-1)
                o = self.output_set[pos]
                trx = transition.Transition(tr_id,
                                            s_start,
                                            s_end,
                                            i, o, '')
                s_start.add_out_transition(trx)
                s_end.add_in_transition(trx)
                transitions.append(trx)
                tr_id = tr_id + 1

        self.transitions = tuple(transitions)

        if save_enabled:
            self.save_fsm('partial_uniform', settings)


    def __partial_random_normal(self, settings, save_enabled, from_=1):
        """
        """
        tr_id = 0
        transitions = []

        first_run = list(range(len(self.states)))
        state_ids = list(range(len(self.states)))

        for s_start in self.states:
            inputs = list(self.input_set)
            random.shuffle(inputs)
            inputs = inputs[from_:]
            for i in inputs:
                s_end = None
                #  The following ensures that each state must have at least
                #  in-degree two but not a loop.
                while first_run:
                    s_end_id = random.randint(0, len(first_run)-1)
                    if s_start.id != first_run[s_end_id]:
                        s_end = self.states[first_run[s_end_id]]

                        if s_end.get_in_degree() > 1:
                            first_run.remove(first_run[s_end_id])
                        break
                    else:
                        if len(first_run) == 1:
                            s_end = self.states[first_run[s_end_id]]
                            first_run = []
                            break

                if s_end is None:                    
                    #  Determining the ending state's ID following Gaussian
                    #  distribution. If pos runs out of the range, then the
                    #  last state is used.
                    s_end_id = abs(int(random.normalvariate(
                        self.num_of_states//2,
                        self.num_of_states//3)))
                    if s_end_id > self.num_of_states - 1:
                        s_end_id = self.num_of_states - 1
                    s_end = self.states[state_ids[s_end_id]]

                pos = abs(int(random.normalvariate(self.num_of_states//2,
                                                   self.num_of_states/3)))
                
                pos = random.randint(0, len(self.output_set)-1)
                o = self.output_set[pos]
                trx = transition.Transition(tr_id,
                                            s_start,
                                            s_end,
                                            i, o, '')
                s_start.add_out_transition(trx)
                s_end.add_in_transition(trx)
                transitions.append(trx)
                tr_id = tr_id + 1
        self.transitions = tuple(transitions)

        if save_enabled:
            self.save_fsm('partial_gauss', settings)


    def set_init_state(self, init_s=0):
        if isinstance(init_s, type(state.State())):
            self.init_state = init_s
            return self.init_state.id

        #  If current_s is a state ID.
        for s in self.states:
            if s.id == init_s:
                self.init_state = s
                return self.current_state


    def set_current_state(self, current_s=0):
        #  If current_s is a state object
        if isinstance(current_s, type(state.State())):
            self.current_state = current_s
            return self.current_state.id

        #  If current_s is a state ID.
        for s in self.states:
            if s.id == current_s:
                self.current_state = s
                return self.current_state


    def reset(self):
        """
        The FSM reset function resets M to its initial state.
            Note: Initial state may not be S0!
        """
        self.current_state = self.init_state


    def get_state(self, s_id):
        for s in self.states:
            if s.id == s_id:
                return s
        return None


    def trigger_trx(self, i):
        for trx in self.current_state.out_trans:
            if i == trx.input:
                self.set_current_state(trx.end_state)
                return trx.output

        #  An error state with id = -1
        self.set_current_state(state.State())
        return None


    def trigger_trxs(self, inputs):
        outputs = []
        for i in inputs:
            o = self.trigger_trx(i)
            outputs.append(o)
            if o is None:
                return outputs
        return outputs


    def copy(self):
        return copy.deepcopy(self)


    def is_minimal(self, MAX_TRIES=5):
        pairs = []

        for i in range(len(self.states)-1):
            for j in range(i+1, len(self.states)):
                pairs.append((i, j))

        for s_i, s_j in pairs:
            i = list(self.input_set) * len(self.states) * 2
            o_str_i = ''
            o_str_j = ''

            distinguishable = False
            tried = 0

            while tried < MAX_TRIES:
                random.shuffle(i)
                i_str = ''.join(i)

                self.set_current_state(s_i)
                o_str_i = self.trigger_trxs(i_str)

                self.set_current_state(s_j)
                o_str_j = self.trigger_trxs(i_str)

                if o_str_i == o_str_j:
                    tried = tried + 1
                else:
                    distinguishable = True
                    break

            if not distinguishable:
                return False

        return True


    def save_fsm(self, shape, settings):
        gen_file_name = self.parms['GeneralFileName']
        fsm_name = [gen_file_name, 'fsm', 'states',
                    (str(self.num_of_states)).zfill(10), shape]
        fsm_name = '_'.join(fsm_name)

        sys_config = self.parms['SysConfig']
        fsm_dir = sys_config['DATA_PATH'] + [gen_file_name]

        suffix = random.randint(10, 99)
        full_name = (os.path.join(*(fsm_dir+[fsm_name])) +
                     '_' + str(suffix) + '.txt')

        while os.path.exists(full_name):
            suffix = random.randint(10, 99)
            full_name = (os.path.join(*(fsm_dir+[fsm_name])) +
                     '_' + str(suffix) + '.txt')

        tmp = sys.stdout
        with open(full_name, 'w') as f:
            sys.stdout = f
            print('states:', self.num_of_states)
            print('input_set'+FSM.SEP, *','.join(self.input_set))
            print('output_set'+FSM.SEP, *','.join(self.output_set))
            print('')
            for tr in self.transitions:
                tr_id = str(tr.id)
                tr_id = tr_id + FSM.SEP + ' '*(5-len(tr_id))
                tr_str = '%d?%d?%s?%s' % (tr.start_state.id, tr.end_state.id, tr.input, tr.output)
                tr_str = tr_str.replace('?', FSM.SEP)
                print(tr_id, tr_str)
        sys.stdout = tmp


    def print_info(self, printing=False):
        width = 50
        prefix = '  '
        
        info = ['-'*width,
                prefix + ('Number of States: ' +
                          str(self.num_of_states)),
                prefix + ('Number of Transitions: ' +
                          str(self.num_of_transitions)),
                prefix + ('Initial State ID: ' +
                          str(self.init_state.id)),
                prefix + ('Current State ID: ' +
                          str(self.current_state.id)),
                ' ']
        for s in self.states:
            info.append(prefix*2 + '- ' + str(s))

        info.append(' ')
        
        for tr in self.transitions:
            info.append(prefix*2 + '[.] ' + str(tr))

        info.append('-'*width)
        info.append(' ')

        info = '\n'.join(info)

        if printing:
            print(info)

        return info


    def __str__(self):
        return self.print_info()


if __name__ == '__main__':
    parms = {'FSM': {},
             'GeneralFileName': 'test_',
             'SysConfig': {'DATA_PATH': []}
             }
    parms['FSM']['FSMDefault'] = {
        'NumberOfStates': 20,
        'InputSet': ['a', 'b', 'c', 'A', 'B', 'C'],
        # 'OutputSet': ['0', '1'],
        'DigraphShapeOptions': ['complete-random-symmetric',
                                'complete-random-uniform',
                                'complete-random-normal',
                                'partial-random-uniform',
                                'partial-random-normal'],
        'DigraphShapeSelection': 4}

    #m = FSM(None, parms, True)
    # print(m)
    
    #flag = m.is_minimal()
    #print(flag)


