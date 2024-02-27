from . import node
from . import layer
import copy


class SST:
    def __init__(self, fsm=None):
        self.fsm = fsm
        self.layers = []

        self.__init_top_layer()


    def __init_top_layer(self):
        if self.fsm is None:
            raise ValueError('FSM is None')

        layer_id = 0
        layer0 = layer.Layer(layer_id)

        n1 = node.Node(layer_id)
        
        self.fsm.set_init_state(self.fsm.states[0])
        self.fsm.set_current_state(self.fsm.states[0])

        n1.fsm_copies.append(self.fsm)
        
        for s in self.fsm.states:
            if s.id == self.fsm.init_state.id:
                continue
            f = self.fsm.copy()
            f.set_init_state(s)
            f.set_current_state(s)
            n1.fsm_copies.append(f)

        n1.trace_splitting()

        layer0.nodes.append(n1)
        self.layers.append(layer0)

        return layer0


    def copy(self):
        return copy.deepcopy(self)


    def reset(self):
        """
        The first layer only contains one node that saves all copies
        of FSMs with different initial state.
        """
        self.layers = self.layers[:1]
        for m in self.layers[0].nodes[0].fsm_copies:
            m.reset()


    def expand_layers(self, inputs, base=1, rule=lambda x: 2*x):
        """
        The input base defines the boundary of the input characters
        for splitting a layer. The rule inut takes a function handler
        to generate the bounary of inputs for the next layer.
        """        
        if inputs == '':
            return 'DONE', ('COMPLETE', '')
        
        layer_inputs = inputs[:base]
        inputs = inputs[base:]
              
        if self.expand_layer(layer_inputs):
            base = rule(base)
            return self.expand_layers(inputs, base, rule)
        else:
            return 'DONE', ('STOP AT INPUTS', layer_inputs)


    def expand_layer(self, inputs):
        """
        The function always reads the last layer and, based upon inputs
        to split nodes.
        """        
        if len(inputs) == 0:
            raise ValueError('Input = "'+inputs+'"')

        current_layer = self.layers[-1]
        if (current_layer.number_of_nodes() > len(inputs)):
            n1 = current_layer.number_of_nodes() // len(inputs)
            n2 = current_layer.number_of_nodes() % len(inputs)
            inputs = (inputs * n1) + inputs[:n2]
        else:
            inputs = inputs[:current_layer.number_of_nodes()]
    
        pair_ups = zip(current_layer.nodes, inputs)

        new_nodes = []
        for n, i in pair_ups:
            splitting_nodes = self.split_node(n, i)
            new_nodes.extend(splitting_nodes)

        if new_nodes == []:
            return False

        layer_x = layer.Layer(current_layer.id+1)

        layer_x.nodes.extend(new_nodes)
        self.layers.append(layer_x)

        return True


    def split_node(self, parent_node, i):
        if not parent_node.splitable():
            return []

        new_nodes = []
        outputs = {}
        
        for m in parent_node.fsm_copies:
            o = m.trigger_trx(i)
            if o in outputs:
                outputs[o].append(m)
            else:
                outputs[o] = [m]

        node_id = 0 
        for o in outputs:
            #  Need to further look at if Dummy Node is needed!!!
            #  if o is None:
            #     continue

            n1 = node.Node(layer_id=parent_node.layer_id+1,
                           id_=node_id)

            n1.input_labels.extend(parent_node.input_labels)
            n1.output_labels.extend(parent_node.output_labels)
            n1.input_labels.append(i)
            n1.output_labels.append(str(o))
            n1.parent = parent_node
            n1.fsm_copies = outputs[o]

            n1.trace_splitting()

            parent_node.children.append(n1)
            new_nodes.append(n1)
            node_id = node_id + 1

        return new_nodes


    def number_of_uios(self):
        num_uios = 0
        for layer in self.layers:
            num_uios = (num_uios +
                        layer.number_of_discrete_nodes())
        return num_uios


    def report_uios(self):
        uios = []
        for layer in self.layers:
            uios.extend(layer.report_uios())
        return uios


    def __str__(self):
        info = []
        for l in self.layers:
            info.append(str(l))
        info.append('')
        return '\n'.join(info)
