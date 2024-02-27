import math
import statistics as st
import matplotlib.pyplot as plt


class UIOStatistics:
    def __init__(self, parms, all_targetted_uios={}):
        self.parms = parms
        self.gens_for_statistics = []
        self.all_targetted_uios = all_targetted_uios
        self.all_discovered_uios = {}
        self.gen_statistics = {}
        self.gen_uio_distribution = {}

        gen_from, interval = parms['GA']['StatisticsGenInterval']
        if interval is None:
            interval = parms['GA']['Generation']
    
        all_gens = list(range(parms['GA']['Generation']))
        gens_collected = all_gens[gen_from:]
        self.gens_for_statistics = gens_collected[:interval]


    def compute_stat(self, gen, pop):
        fitnesses = [ind[0]['fitness'] for ind in pop]
        f_max = max(fitnesses)
        f_min = min(fitnesses)
        f_mean = st.mean(fitnesses)
        f_std = st.stdev(fitnesses)
        self.gen_statistics[gen] = (f_max, f_min, f_mean, f_std)


    def compute_UIO_distribution(self, gen, pop):
        """
        A dictionary uios is defined to store that numbers of SSTs that
        have explored 1, 2, ..., n UIOs respectively.
        """
        uios = {}
        for ind in pop:
            sst = ind[0]['sst']
            num = sst.number_of_uios()
            uios[num] = uios.get(num, 0) + 1
        self.gen_uio_distribution[gen] = uios


    def composite_avg_uio_distribution(self):
        uio_avg = {}
        for gen in self.gens_for_statistics:
            uio_data = self.gen_uio_distribution[gen]

            for num_of_uios in uio_data:
                uio_avg[num_of_uios] = (uio_avg.get(num_of_uios, 0) +
                                        uio_data[num_of_uios])

        for num_of_uios in uio_avg:
            uio_avg[num_of_uios] = (uio_avg[num_of_uios] /
                                    len(self.gens_for_statistics))

        return uio_avg


    def process(self, gen, pop):
        self.compute_stat(gen, pop)
        self.compute_UIO_distribution(gen, pop)


    def plot_trendency_graph(self, save=None):
        gens = sorted(self.gen_statistics.keys())
        fitness_max = [self.gen_statistics[gen][0] for gen in gens]
        fitness_min = [self.gen_statistics[gen][1] for gen in gens]
        fitness_avg = [self.gen_statistics[gen][2] for gen in gens]
        fitness_std = [self.gen_statistics[gen][3] for gen in gens]

        fig, axes = plt.subplots()
        fig.suptitle('-- UIO statistical measurements --')
        axes.plot(gens, fitness_max, color='black', label='MAX')
        axes.plot(gens, fitness_min, color='cyan', label='MIN')
        axes.plot(gens, fitness_avg, color='blue', label='MEAN')
        axes.plot(gens, fitness_std, color='red', label='STDEV')
        axes.set_xlabel('Generations')
        axes.set_ylabel('Statistics')
        axes.legend(loc="upper right")

        if save:
            fig.savefig(save)
        else:
            fig.show()


    def plot_UIO_distribution(self, save=None):
        collection = self.composite_avg_uio_distribution()

        nums = sorted(collection.keys())
        data = [collection[n] for n in nums]
        labels = ['UIOs: '+str(i) for i in nums]
        explode = [0.05 for _ in nums]


        fig, axes = plt.subplots()
        fig.suptitle('-- SST UIO partitioning distributions --')
        axes.pie(data,
                labels=nums,
                explode=explode)
        axes.legend(title = "UIOs in SSTs",
                   labels=labels,
                   loc='upper left',
                   bbox_to_anchor=(1, 0.85))

        if save:
            plt.savefig(save)
        else:
            plt.show()



    def get_info(self, pt=False):
        info = []
        for gen in self.gen_statistics:
            d = 'Gen{0:>5}: {1}'.format(gen, self.gen_statistics[gen])
            info.append(d)
            uio_info = []
            for uio_num in self.gen_uio_distribution[gen]:
                uio_info.append('  ' + str(self.gen_uio_distribution[gen][uio_num]) +
                                ' -> SST UIOs (' + str(uio_num) + '): ')
            info.extend(uio_info)

        info = '\n'.join(info)

        if pt:
            print(info)
        return info
