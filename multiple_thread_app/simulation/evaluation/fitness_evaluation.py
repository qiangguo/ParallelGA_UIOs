import math


class FitnessEvaluation:
    def __init__(self, parms={}):
        self.parms = parms
        self.sd_func = None

        self.__inst()


    def __inst(self):
        index = self.parms['GA']['TreeInputRule']
        self.sd_func = eval(self.parms['SSTLayerInputRules'][index])


    def similarity(self, ind1, ind2, base=1, prv_sd=1, n=1, sd=0):
        if ind1 == '' or ind2 == '':
            return sd / n

        cmp1 = ind1[:base]
        ind1 = ind1[base:]
        
        cmp2 = ind2[:base]
        ind2 = ind2[base:]

        #  We can propose parallel here ...
        current_sd = 0
        for i in range(len(cmp1)):
            if cmp1[i] == cmp2[i]:
                current_sd = current_sd + 1
        current_sd = prv_sd * (current_sd / len(cmp1))

        base = self.sd_func(base)

        return self.similarity(ind1, ind2, base, current_sd, n+1, sd+current_sd)


    def __scaling(self, val, enabled=True):
        if enabled:
            b = self.parms['Fitness']['ScalingBase']
            val = math.log(val, b)
            """
            try:
                val = ((math.pow(b, val) - math.pow(b, -1*val)) /
                       (math.pow(b, val) + math.pow(b, -1*val)))
            except Exception as e:
                #  print('  >>> ', str(e), val)
                #  Prevent overflow!
                val = math.log(val, b)
            """

        return val


    def __single_layer_eval(self, layer, prv_xi, prv_yi):
        delta_xi = 0
        delta_yi = 0

        for node in layer.nodes:
            if node.is_discrete():
                delta_xi = delta_xi + 1
            else:
                delta_yi = delta_yi + 1

        xi = prv_xi + delta_xi
        yi = prv_yi + delta_yi

        #  We can extract layer depth from the layer ID.
        comp_exp = (xi * math.pow(math.e, delta_xi)/
                    math.pow(layer.id, self.parms['Fitness']['Gammar']))

        p = (self.parms['Fitness']['LayerHeightThreshold'] -
             math.pow(layer.id+1, self.parms['Fitness']['Belta']) +
             delta_xi / (layer.id+1))

        decay_val = math.pow(math.e, p)

        comp_linear = self.parms['Fitness']['Alpha'] * yi * decay_val

        fitness = comp_exp + comp_linear

        return (xi, yi, fitness)


    def layer_based_fitness(self, layers, n=1.0,
                            x=0, y=1, fitness=0, scaling_enabled=True):
        """
        The function returns its original fitness value and the scaled fitness
        value while the latter is used for selection.
        """
        if layers == []:
            return (fitness/n,
                    self.__scaling(fitness/n, enabled=scaling_enabled))

        layer, *layers = layers

        x, y, f = self.__single_layer_eval(layer, x, y)

        return self.layer_based_fitness(layers, n, x, y, fitness+f,
                                        scaling_enabled=scaling_enabled)


    def eval_sst(self, attr, scaling_enabled=True):
        sst = attr['sst']

        return self.layer_based_fitness(sst.layers[1:],
                                        len(sst.layers),
                                        scaling_enabled=scaling_enabled)



    
