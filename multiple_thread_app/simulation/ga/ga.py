import random
import copy
import threading


class GA:
    def __init__(self, fsm, sst, parms={}):
        self.fsm = fsm
        self.sst = sst
        self.parms = parms
        self.splitting_rule = None
        self.chromosome_length = -1

        self.population_buffers = ([], [])
        self.active_pop = -1

        sel = self.parms['GA']['SelectionOperator']
        self.selection = eval('self.'+self.parms['GASelectMethods'][sel])

        sel = self.parms['GA']['XOverOperator']
        self.crossover = eval('self.'+self.parms['GAXOverMethods'][sel])

        sel = self.parms['GA']['MutationOperator']
        self.mutation = eval('self.'+self.parms['GAMutationMethods'][sel])
 
        self.__instantiate()


    def __parallise_construct(self, func, args=(), step=1):
        pop_size = self.parms['GA']['PopulationSize']
        reminder = pop_size
        cpus = self.parms['SysConfig']['CPUs']
        threads = cpus * self.parms['NumberOfThreadsPerCPU']
        base = 0

        while reminder > 0:
            to = min([base+threads*step, pop_size])
            X = range(base, to, step)
            reminder = reminder - len(X)*step

            for i in X:
                new_args = (i, *args)
                t = threading.Thread(target=func, args=new_args)
                t.start()
                t.join()
            base = to


    def __individual_init(self, id_):
        """
        Initialise a single chromosome and insert it to populations.
        """
        inputs = list(self.fsm.input_set)
        inputs = inputs * self.chromosome_length

        for _ in range(5):
            random.shuffle(inputs)

        inputs = ''.join(inputs[:self.chromosome_length])
        self.population_buffers[0][id_] = (self.parms["ChromosomeAttributes"],
                                           inputs)
        self.population_buffers[1][id_] = (self.parms["ChromosomeAttributes"],
                                           ' '*self.chromosome_length)


    def __instantiate(self):
        """
        This internal function converts SST splitting rule, GA selection,
        Crossover, and Mutation operators to their corresponding functions
        from the parameter configuration.
        """
        
        #  Extract SST splitting rule
        i = self.parms['GA']['TreeInputRule']
        self.splitting_rule = eval(self.parms['SSTLayerInputRules'][i])

        base = [1]
        for _ in range(self.parms['MaxUIOLength']-1):
            base.append(self.splitting_rule(base[-1]))

        #  Calculate the chromosome length based upon SST splitting rule.
        self.chromosome_length = sum(base)

        #  Extract Selection, XOver and Mutation operators
        sel = self.parms['GA']['SelectionOperator']
        self.selection = eval('self.'+self.parms['GASelectMethods'][sel])

        sel = self.parms['GA']['XOverOperator']
        self.crossover = eval('self.'+self.parms['GAXOverMethods'][sel])

        sel = self.parms['GA']['MutationOperator']
        self.mutation = eval('self.'+self.parms['GAMutationMethods'][sel])

        #  Initialise population
        pop_size = self.parms['GA']['PopulationSize']
        for _ in range(pop_size):
            self.population_buffers[0].append('')
            self.population_buffers[1].append('')

        #  ------------------------------------------------------------
        #  Parallise init
        #  ------------------------------------------------------------
        if self.parms['ParallelismEnabled']:
            self.__parallise_construct(self.__individual_init)
        else:
            for i in range(pop_size):
                self.__individual_init(i)

        #  Set the active population to index 0.
        self.active_pop = 0


    def get_target_pop(self):
        """
        Based upon the current active population index, the function returns
        the index for the target population.
        """
        return (self.active_pop + 1) % 2


    def update_active_pop(self):
        """
        This function swaps between GA active population and the target
        population. It works as a pendulum
        """
        self.active_pop = (self.active_pop + 1) % 2


    def produce_single_sst(self, id_):
        """
        The function produces an SST based upon the input sequence.
        """
        ind_attr, inputs = self.population_buffers[self.active_pop][id_]
        sst = self.sst.copy()
        sst.expand_layers(inputs, rule=self.splitting_rule)
        attr = copy.deepcopy(ind_attr)
        attr['sst'] = sst
        self.population_buffers[self.active_pop][id_] = (attr, inputs)


    def produce_all_ssts(self):
        if self.parms['ParallelismEnabled']:
            return self.__parallise_construct(self.produce_single_sst)
        else:
            for i in range(self.parms['GA']['PopulationSize']):
                self.produce_single_sst(i)



    def evaluate_fitness_by_one(self, i, fitness_eval, scaling_enabled):
        ind = self.population_buffers[self.active_pop][i]
        attr = copy.deepcopy(ind[0])
        fitness, scaled_fitness = fitness_eval.eval_sst(attr, scaling_enabled)
        attr['fitness'] = fitness
        attr['scaled_fitness'] = scaled_fitness
        self.population_buffers[self.active_pop][i] = (attr, ind[1])


    def evaluate_all_fitness(self, fitness_eval):
        """
        This function evaluates each individual in the active GA population and
        computes its fitness value. If fitness scaling is enabled in the parms
        configuration, then the fitness value will be scaled by the scaling
        function defined inside the fitness module..
        """
        scaling_enabled = self.parms['GA']['ScalingEnabled']

        if self.parms['ParallelismEnabled']:
            args = (fitness_eval, scaling_enabled)
            return self.__parallise_construct(self.evaluate_fitness_by_one,
                                              args)
        pop_size = len(self.population_buffers[self.active_pop])
        for i in range(pop_size):
            self.evaluate_fitness_by_one(i,
                                         fitness_eval,
                                         scaling_enabled=scaling_enabled)


    def normalise_fitness_by_one(self, i, s):
        """
        Normalise individual fitness to the range [0, 1]
        """
        ind = self.population_buffers[self.active_pop][i]
        #  Be careful! If not using copy(), a reference is passed!
        attr = copy.deepcopy(ind[0])
        attr['scaled_fitness'] = attr['scaled_fitness'] / s
        self.population_buffers[self.active_pop][i] = (attr, ind[1])


    def normalise_all_scaled_fitness(self):
        s = sum([ind[0]['scaled_fitness']
                 for ind in self.population_buffers[self.active_pop]])

        if self.parms['ParallelismEnabled']:
            args = (s, )
            return self.__parallise_construct(self.normalise_fitness_by_one,
                                              args)
        pop_size = len(self.population_buffers[self.active_pop])
        for i in range(pop_size):
            self.normalise_fitness_by_one(i, s)



    def selection_rws_by_one(self, id_, target_pop):
        fitness_acc = 0
        threhold_val = random.random()        
        pop_size = len(self.population_buffers[target_pop])

        while True:
            i = random.randint(0, pop_size-1)
            s_ind = self.population_buffers[self.active_pop][i]

            fitness_acc = fitness_acc + s_ind[0]['scaled_fitness']
            if fitness_acc > threhold_val:
                self.population_buffers[target_pop][id_] = copy.deepcopy(s_ind)
                break


    def selection_rws(self):
        target_pop = self.get_target_pop()

        if self.parms['ParallelismEnabled']:
            args = (target_pop, )
            self.__parallise_construct(self.selection_rws_by_one, args)
        else:
            for i in range(len(self.population_buffers[target_pop])):
                self.selection_rws_by_one(i, target_pop)

        self.update_active_pop()


    def selection_ts_by_one(self, id_, target_pop, ts_portion):
        """
        Tournament selectin for a single candidate. It randomly chooses a
        portion of candidates from the population and selects the best for
        the next generation.
        """
        pop_size = len(self.population_buffers[target_pop])
        portion_size = int(ts_portion * pop_size)

        candidate = None

        # This can be further parallised with parallely sampling candidates
        for _ in range(portion_size):
            i = random.randint(0, pop_size-1)
            if candidate is None:
                candidate = self.population_buffers[self.active_pop][i]
            else:
                ind = self.population_buffers[self.active_pop][i]
                if ind[0]['scaled_fitness'] > candidate[0]['scaled_fitness']:
                    candidate = ind
        self.population_buffers[target_pop][id_] = copy.deepcopy(candidate)


    def selection_ts(self):
        """
        Tournament selection for a simple GA. It works on sampling a portion of
        the population and then chooses the one with the highest fitness as its
        candidate.
        """
        target_pop = self.get_target_pop()
        portion = self.parms['GA']['TS_SelectionPortion']

        if self.parms['ParallelismEnabled']:
            args = (target_pop, portion)
            self.__parallise_construct(self.selection_ts_by_one, args)
        else:
            for i in range(len(self.population_buffers[target_pop])):
                self.selection_ts_by_one(i, target_pop, portion)

        self.update_active_pop()


    def xover_single_by_one(self, id_, target_pop):
        l = len(self.population_buffers[target_pop])
        c_id_1 = random.randint(0, l-1)
        c_id_2 = c_id_1

        while c_id_2 == c_id_1:
            c_id_2 = random.randint(0, l-1)

        threshold = random.random()
        if threshold > self.parms['GA']['XRate']:
            ind_1 = (self.parms["ChromosomeAttributes"],
                     self.population_buffers[self.active_pop][c_id_1][1])
            ind_2 = (self.parms["ChromosomeAttributes"],
                     self.population_buffers[self.active_pop][c_id_2][1])
        else:
            cutting = random.randint(1, self.chromosome_length-1)
            c1 = list(self.population_buffers[self.active_pop][c_id_1][1])
            c2 = list(self.population_buffers[self.active_pop][c_id_2][1])
            c_new_1 = c1[:cutting] + c2[cutting:]
            c_new_2 = c2[:cutting] + c1[cutting:]

            ind_1 = (self.parms["ChromosomeAttributes"], ''.join(c_new_1))
            ind_2 = (self.parms["ChromosomeAttributes"], ''.join(c_new_2))

        self.population_buffers[target_pop][id_] = ind_1
        self.population_buffers[target_pop][id_+1] = ind_2


    def xover_single(self):
        """
        Single point crossover operation works on randomly choosing a cutting
        point betwen [1, length-1] and then perform bitwise based mutation.
        """
        target_pop = self.get_target_pop()
        if self.parms['ParallelismEnabled']:
            args = (target_pop, )
            self.__parallise_construct(self.xover_single_by_one, args, 2)
        else:
            for i in range(0, len(self.population_buffers[target_pop]), 2):
                self.xover_single_by_one(i, target_pop)

        self.update_active_pop()



    def xover_multiple_by_one(self, id_, target_pop):
        l = len(self.population_buffers[target_pop])
        c_id_1 = random.randint(0, l-1)
        c_id_2 = c_id_1

        while c_id_2 == c_id_1:
            c_id_2 = random.randint(0, l-1)

        threshold = random.random()
        if threshold > self.parms['GA']['XRate']:
            ind_1 = (self.parms["ChromosomeAttributes"],
                     self.population_buffers[self.active_pop][c_id_1][1])
            ind_2 = (self.parms["ChromosomeAttributes"],
                     self.population_buffers[self.active_pop][c_id_2][1])
        else:
            cuttings = list(range(1, self.chromosome_length))
            cuttings = list(range(1, self.chromosome_length))
            random.shuffle(cuttings)
            cuttings = cuttings[:self.parms['GA']['MultipleXOverPoints']]
            cuttings.sort()

            candidates = [self.population_buffers[self.active_pop][c_id_1][1],
                          self.population_buffers[self.active_pop][c_id_2][1]]

            start = 0
            turn = 0
            c_new_1 = ''
            c_new_2 = ''
            cuttings.append(self.chromosome_length+1)
            
            while cuttings:
                point, *cuttings = cuttings
                c_new_1 = c_new_1 + candidates[turn][start:point]
                c_new_2 = c_new_2 + candidates[(turn+1)%2][start:point]
                start = point
                turn = (turn + 1) % 2

            ind_1 = (self.parms["ChromosomeAttributes"], c_new_1)
            ind_2 = (self.parms["ChromosomeAttributes"], c_new_2)

        self.population_buffers[target_pop][id_] = ind_1
        self.population_buffers[target_pop][id_+1] = ind_2



    def xover_multiple(self):
        """
        Multiple point crossover operation works on randomly choosing a set of
        cutting points betwen [1, length-1] and then perform bitwise based
        mutation. The number of cutting points is predefined in parameters.
        """
        target_pop = self.get_target_pop()
        if self.parms['ParallelismEnabled']:
            args = (target_pop, )
            self.__parallise_construct(self.xover_multiple_by_one, args, 2)
        else:
            for i in range(0, len(self.population_buffers[target_pop]), 2):
                self.xover_multiple_by_one(i, target_pop)

        self.update_active_pop()


    def xover_uniform_by_one(self, id_, target_pop):
        l = len(self.population_buffers[target_pop])
        c_id_1 = random.randint(0, l-1)
        c_id_2 = c_id_1

        while c_id_2 == c_id_1:
            c_id_2 = random.randint(0, l-1)

        threshold = random.random()
        if threshold > self.parms['GA']['XRate']:
            ind_1 = (self.parms["ChromosomeAttributes"],
                     self.population_buffers[self.active_pop][c_id_1][1])
            ind_2 = (self.parms["ChromosomeAttributes"],
                     self.population_buffers[self.active_pop][c_id_2][1])
        else:
            c1 = list(self.population_buffers[self.active_pop][c_id_1][1])
            c2 = list(self.population_buffers[self.active_pop][c_id_2][1])

            masks = [random.randint(0, 1) for _ in range(self.chromosome_length)]
            
            c_new_1 = [c1[i] if not masks[i] else c2[i]
                           for i in range(self.chromosome_length)]
            c_new_2 = [c1[i] if masks[i] else c2[i]
                           for i in range(self.chromosome_length)]

            ind_1 = (self.parms["ChromosomeAttributes"], ''.join(c_new_1))
            ind_2 = (self.parms["ChromosomeAttributes"], ''.join(c_new_2))

        self.population_buffers[target_pop][id_] = ind_1
        self.population_buffers[target_pop][id_+1] = ind_2


    def xover_uniform(self):
        target_pop = self.get_target_pop()
        if self.parms['ParallelismEnabled']:
            args = (target_pop, )
            self.__parallise_construct(self.xover_uniform_by_one, args, 2)
        else:
            for i in range(0, len(self.population_buffers[target_pop]), 2):
                self.xover_uniform_by_one(i, target_pop)

        self.update_active_pop()


    def mutate_bitwise_by_one(self, id_, target_pop):
        threshold = random.random()
        ind = self.population_buffers[self.active_pop][id_]

        if threshold > self.parms['GA']['MRate']:
            self.population_buffers[target_pop][id_] = copy.deepcopy(ind)
        else:
            mut_i = random.randint(0, self.chromosome_length-1)
            candidates = list(self.fsm.input_set)
            candidates.remove(ind[1][mut_i])
            random.shuffle(candidates)
            input_str = ind[1][:mut_i] + candidates[0] + ind[1][mut_i+1:]
            self.population_buffers[target_pop][id_] = (
                (self.parms["ChromosomeAttributes"], input_str))


    def mutate_bitwise(self):
        target_pop = self.get_target_pop()
        if self.parms['ParallelismEnabled']:
            args = (target_pop, )
            self.__parallise_construct(self.mutate_bitwise_by_one, args)
        else:
            for i in range(len(self.population_buffers[target_pop])):
                self.mutate_bitwise_by_one(i, target_pop)

        self.update_active_pop()        


    def mutate_torus_by_one(self, id_, target_pop, base, settings):
        threshold = random.random()
        ind = self.population_buffers[self.active_pop][id_]
        if threshold > self.parms['GA']['MRate']:
            self.population_buffers[target_pop][id_] = copy.deepcopy(ind)
        else:
            degree = settings['Degree']
            ind_str_mut = ind[1]
            ind_str_mut = ind_str_mut[degree:] + ind_str_mut[0:degree]
            self.population_buffers[target_pop][id_] = (
                (self.parms["ChromosomeAttributes"], ind_str_mut))

    
    def mutate_torus_by_one_1(self, id_, target_pop, base, settings):
        threshold = random.random()
        ind = self.population_buffers[self.active_pop][id_]
        
        if threshold > self.parms['GA']['MRate']:
            self.population_buffers[target_pop][id_] = copy.deepcopy(ind)
        else:
            f_mut = settings['MutateFunc']
            degree = settings['Degree']

            mut_p = random.randint(1, len(base)-1)
            start_point = base[mut_p] - 1
            end_point = 2 * base[mut_p] - 1

            ind = self.population_buffers[self.active_pop][id_]
            ind_org_substr = ind[1][start_point:end_point]
            ind_mut_substr = list(ind_org_substr)

            # f_mut supports shuffle of a list. In such a case, the return is
            # None with the input list being shuffled.
            for _ in range(degree):
                v = f_mut(ind_mut_substr)
                if v is not None:
                    ind_mut_substr = v[:]

            ind_mut_substr = ''.join(ind_mut_substr)
            ind_str_mut = (ind[1][:start_point] +
                           ind_mut_substr +
                           ind[1][end_point:])
            self.population_buffers[target_pop][id_] = (
                (self.parms["ChromosomeAttributes"], ind_str_mut))


    def mutate_torus(self):
        base = [1]
        for _ in range(self.parms['MaxUIOLength']-1):
            base.append(self.splitting_rule(base[-1]))

        rules = self.parms["LayerBasedMutationRules"]
        sel = self.parms["GA"]["MutationOperatorRule"]

        f_mut = eval(rules[sel])
        degree = self.parms["GA"]["MutationOperatorDegree"]
        
        settings = {'MutateFunc': f_mut,
                    'Degree': degree}
        
        target_pop = self.get_target_pop()
        if self.parms['ParallelismEnabled']:
            args = (target_pop, base, settings)
            self.__parallise_construct(self.mutate_torus_by_one, args)
        else:
            for i in range(len(self.population_buffers[target_pop])):
                self.mutate_torus_by_one(i, target_pop, base, settings)

        self.update_active_pop()


    def sd(self, input_a, input_b, fitness_eval, measure=[0]):
        """
        This function measures the Similarity Degree (SD) between two input
        sequences based upon the SST layer-based splitting rule. It takes a
        list 'measure' as one input where sd contains only one value. This aims
        to bring in a mutable data structure to store value for parallel the
        parallelism. When establishing multi-thread based computational model,
        sd is used to pass and store computational results.
        """
        measure[0] = fitness_eval.similarity(input_a, input_b)
        return measure[0]


    #  TODO: we need to consider parallise evaluations of SD
    def sharing_by_one(self, id_, fitness_eval):
        """
        This function compares and reports the SD between the individual with
        id_ and all its ancestors, i.e., individuals with id < id_. This aims
        to count how many times the current candidate has been represented by
        its ancestors. The more times it has been represented, the higher
        degree it should be downgraded.
        """
        ind = self.population_buffers[self.active_pop][id_]

        #  TODO: can be further parallised here ...
        for i in range(id_):
            ind_prv = self.population_buffers[self.active_pop][i]
            # -----------------------------------------------------
            #       The following is for parallesim
            # -----------------------------------------------------
            #  m = [0]
            #  self.sd(ind1[1], ind2[1], fitness_eval, m)
            #  m_sd = m[0]
            # -----------------------------------------------------
            m_sd = self.sd(ind[1], ind_prv[1], fitness_eval)

            #  If a measurement passes the threshold, then we include it to the
            #  list of candidates for sharing downgrading.
            if m_sd > self.parms['GA']['SimilarityThreshold']:
                ind[0]['sharing_factors'].append(m_sd)


    def sharing(self, fitness_eval):
        """
        The sharing function creates a 2D array to store pair-up based
        similarity among individuals.
        """
        if self.parms['ParallelismEnabled']:
            args = (fitness_eval, )
            self.__parallise_construct(self.sharing_by_one, args)
        else:
            #  There is no need to perform sharing operation for the first one.
            for i in range(1, self.parms['GA']['PopulationSize']):
                self.sharing_by_one(i, fitness_eval)

        #  If sharing_factors list is not empty, then the individual's fitness
        #  is first downgraded by the max factor and then divided by the number
        #  of times this candidate has been represented by its ancestors.

        for ind in self.population_buffers[self.active_pop]:
            if ind[0]['sharing_factors'] != []:
                max_factor = max(ind[0]['sharing_factors'])
                ind[0]['scaled_fitness'] = (((1 - max_factor) *
                                             ind[0]['scaled_fitness']) /
                                            len(ind[0]['sharing_factors']))


    def collect_uios(self, stat, gen):
        """
        The function collects and reports all UIOs discovered from this
        generation. The variable uio_counts saves the frequency of occurrences
        of the input part of a group of UIO sequences; the variable all_uios
        saves all UIOs and their corresponding identified states.
        """
        uios = []

        for ind in self.population_buffers[self.active_pop]:
            frequencies = {}
            sst_pattern = ind[0]['sst']

            discovered_uios = sst_pattern.report_uios()            
            for _s, i, _o in discovered_uios:
                frequencies[i] = frequencies.get(i, 0) + 1


            uios.extend(discovered_uios)

            if frequencies == {}:
                ind[0]['sharing_factors'].append(0.999)


        for uio in uios:
            s, i, o = uio
            stat.all_discovered_uios[s] = list(
                set(stat.all_discovered_uios.get(s, []) + [(i, o)]))



    def process_individuals(self, fitness_eval, stat, gen=0):
        self.produce_all_ssts()

        #  TODO: need to propose a parallel data structure for collecting UIOs.
        self.collect_uios(stat, gen)
        self.evaluate_all_fitness(fitness_eval)


        self.normalise_all_scaled_fitness()

        if self.parms['GA']['SharingEnabled']:
            self.sharing(fitness_eval)
            self.normalise_all_scaled_fitness()


        #  TODO: consider parallising the statistical computations
        if self.parms['GA']['StatisticsEnabled']:
            stat.process(gen, self.population_buffers[self.active_pop])


    def start(self, fitness_eval, stat):
        self.process_individuals(fitness_eval, stat, gen=0)

        if self.parms['DebugEnabled']:
            with open('trace.txt', 'a') as fn:
                i = 0
                for sst, ind in self.population_buffers[self.active_pop]:
                    fn.write(str(i) + ': ' + ind + ' - ' +
                             str(sst['fitness']) + ':' +
                             str(sst['scaled_fitness']) +
                             ' @ ' + str(sst['sharing_factors']))
                    fn.write('\n')
                    i = i + 1

                i = 0
                fn.write('-'*30)
                fn.write('\n')
                for _, ind in self.population_buffers[(self.active_pop+1) % 2]:
                    fn.write(str(i) + ': ' + ind)
                    fn.write('\n')
                    i = i + 1
                fn.write('~'*40)
                fn.write('\n'*3)

        for gen in range(1, self.parms['GA']['Generation']):
            if self.parms['DebugEnabled']:
                print('       => Generation: ', gen)
            self.selection()
            self.crossover()
            self.mutation()
            self.process_individuals(fitness_eval, stat, gen)


            if self.parms['DebugEnabled']:
                with open('trace.txt', 'a') as fn:
                    i = 0
                    for sst, ind in self.population_buffers[self.active_pop]:
                        fn.write(str(i) + ': ' + ind + ' - ' +
                                 str(sst['fitness']) + ':' +
                                 str(sst['scaled_fitness']) +
                                 ' @ ' + str(sst['sharing_factors']))
                        fn.write('\n')
                        i = i + 1
                    fn.write('-'*30)
                    fn.write('\n')
                    i = 0
                    for _, ind in self.population_buffers[(self.active_pop+1) % 2]:
                        fn.write(str(i) + ': ' + ind)
                        fn.write('\n')
                        i = i + 1
                    fn.write('\n'*3)
                    fn.write('~'*40)
                    fn.write('\n'*3)


    def parms_info(self, debug=False):
        info = []
        template = "%s%s %s"
        for key in self.parms:
            if isinstance(self.parms[key], dict):
                info.append(template % (key, "=>", ''))
                for subkey in self.parms[key]:
                    info.append('  '+template %
                                (subkey, ":", self.parms[key][subkey]))
            else:
                info.append(template % (key, ":", self.parms[key]))

        info = '\n'.join(info)
        if debug:
            print(info)

        return info


    def __test_display(self):
        print("Active", self.active_pop)
        for ind in self.population_buffers[self.active_pop]:
            print(ind)

        print("\n")

        print("Target", self.get_target_pop())
        for ind in self.population_buffers[self.get_target_pop()]:
            print(ind)

        print("-"*30)
        print()
