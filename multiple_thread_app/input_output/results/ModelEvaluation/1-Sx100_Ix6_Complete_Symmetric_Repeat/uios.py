import os
import matplotlib.pyplot as plt
import numpy as np


Cat = 'Repeating Completely Specified Symmetric FSM'



D = ['20231201_171621_349915',
     '20231216_174711_549743',
     '20231216_174730_224218',
     '20231216_174736_188200',
     '20231216_174756_846951']

Fs = {'20231201_171621_349915': 'FSM 1',
      '20231216_174711_549743': 'FSM 2',
      '20231216_174730_224218': 'FSM 3',
      '20231216_174736_188200': 'FSM 4',
      '20231216_174756_846951': 'FSM 5'}




def get_uios():
    data = {}
    for d in Fs:
        f = os.path.join(d, d+'_uio.txt')
        with open(f, 'r') as fn:
            uios = fn.readline()
            uios = eval(uios)
            data[d] = uios
    return data




def count_uios(data):
    results = {}
    for d in data:
        uios = data[d]
        states = sorted(uios)
        collection = {}
        for s in states:
            s_label = 'S'+str(s)
            num_of_uios = len(uios[s])
            collection[s_label] = num_of_uios
        results[d] = collection

    return results



def merge_uios(data):
    ST = {}
    for dt in data:
        for s in data[dt]:
            x = ST.get(s, [])
            ST[s] = x + data[dt][s]
            ST[s] = list(set(ST[s]))
            
    return ST



def cal_gaps(data, merged_data):
    for dt in data:
        for s in data[dt]:
            gap = len(merged_data[int(s[1:])]) - data[dt][s]
            data[dt][s] = [data[dt][s], gap]



def produce_gap_bar_chart(data):
    for dt in data:
        labels = list(data[dt].keys())
        values = list(data[dt].values())
        found_uios = [v[0] for v in values]
        missed_uios = [v[1] for v in values]
        fig, ax = plt.subplots(figsize=(10, 7))
        
        ax.bar(labels,
               found_uios,
               color=["blue"],
               label="Number of Found UIOs",
               align='edge',
               width=0.4)
        ax.bar(labels,
               missed_uios,
               color=["lightgrey"],
               bottom=found_uios,
               label="Number of Missed UIOs",
               align='edge',
               width=0.4)
        ax.set_title("Number of Found UIOs vs. Number of Missed UIOs", fontsize=15)
        x_pos = np.arange(len(values))
        plt.xticks(x_pos, labels, rotation=75, fontsize=5, fontname='serif')
        ax.set_ylabel("Number of UIOs")

        ax.legend()
        plt.show()

        
        """
        fname = Cat.split()[:4] + [Fs[dt]]
        fname = '_'.join(fname)
        fname = fname.replace(' ', '_') + '.png'
        plt.savefig(fname)
        """




data = get_uios()
merged_data = merge_uios(data)

results = count_uios(data)

cal_gaps(results, merged_data)
produce_gap_bar_chart(results)


def test():
    x = ["A", "B", "C", "D", "E", "F", "G", "H"]
    y = [150, 85.2, 65.2, 85, 45, 120, 51, 64]


    shops = ["A", "B", "C", "D", "E", "F"]
    sales_product_1 = [100, 85, 56, 42, 72, 15]
    sales_product_2 = [50, 120, 65, 85, 25, 55]
    sales_product_3 = [20, 35, 45, 27, 55, 65]

    fig, ax = plt.subplots(figsize=(10, 7))
    # 
    ax.bar(shops, sales_product_1, color="red", label="Product_1")
    # 
    ax.bar(shops, sales_product_2, color="blue", bottom=sales_product_1, label="Product_2")
    # 
    ax.bar(shops, sales_product_3, color="green", 
           bottom=np.array(sales_product_2) + np.array(sales_product_1), label="Product_3")

    ax.set_title("Stacked Bar plot", fontsize=15)
    ax.set_xlabel("Shops")
    ax.set_ylabel("Product Sales")
    ax.legend()

    plt.show()


#test()




