import os
import matplotlib.pyplot as plt
import numpy as np


Cat = 'Completely Specified Symmetric Random FSM'

D = ['20231201_162332_803264',
     '20231201_171621_349915',
     '20231201_171748_110243',
     '20231201_171858_817528',
     '20231201_171941_123750']

Fs = {'20231201_162332_803264': 'FSM 1',
      '20231201_171621_349915': 'FSM 2',
      '20231201_171748_110243': 'FSM 3',
      '20231201_171858_817528': 'FSM 4',
      '20231201_171941_123750': 'FSM 5'}




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
        


def plot_uios(d, UIOs):
    labels = list(UIOs.keys())
    values = list(UIOs.values())

    min_val, max_val = min(values), max(values)
    l = 'Numbers of UOs: Min={}, Max={}'
    
    height = values
    bars = labels
    x_pos = np.arange(len(bars))

    plt.bar(x_pos, height, color=['blue'], align='edge', width=0.4)
    plt.xticks(x_pos, bars, rotation=75, fontsize=5, fontname='serif')
    plt.legend([l.format(min_val, max_val)])

    plt.xlabel("FSM States")
    plt.ylabel("Number of UIOs")

    plt.title('UIOs Constructed from ' + Cat)


    plt.show()

    return 

    fname = Cat.split()[:4] + [Fs[d]]
    fname = '_'.join(fname)
    fname = fname.replace(' ', '_') + '.png'
    plt.savefig(fname)


data = get_uios()

results = count_uios(data)



"""
for k in results:
    print(k)
    for s in results[k]:
        print('    ', s, ':', results[k][s])
    print('\n\n')
"""


for k in results:
    plot_uios(k, results[k])


"""
def plot_uios(UIOs):
    # nums = list(range(100))

    labels = UIOs.keys()
    values = UIOs.values()

    min_val, max_val = min(values), max(values)
    l = 'Numbers of UOs: Min={}, Max={}'
    
    height = values
    bars = labels
    x_pos = np.arange(len(bars))

    plt.bar(x_pos, height, color=['blue'])
    plt.xticks(x_pos, bars, rotation=75, fontsize=8, fontname='serif')
    plt.legend([l.format(min_val, max_val)])

    plt.xlabel("FSM States")
    plt.ylabel("Number of UIOs")

    plt.title(Cat+Fs[D[0]])


    plt.show()
    
"""
"""
def test():
    x = ["A", "B", "C", "D", "E", "F", "G", "H"]
    y = [150, 85.2, 65.2, 85, 45, 120, 51, 64]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.bar(x=x, height=y)
    ax.set_title("Simple Bar Plot", fontsize=15)

    shops = ["A", "B", "C", "D", "E", "F"]
    sales_product_1 = [100, 85, 56, 42, 72, 15]
    sales_product_2 = [50, 120, 65, 85, 25, 55]
    sales_product_3 = [20, 35, 45, 27, 55, 65]

    fig, ax = plt.subplots(figsize=(10, 7))
    # 先创建一根柱子，显示第一种产品的销量
    ax.bar(shops, sales_product_1, color="red", label="Product_1")
    # 第二根柱子“堆积”在第一根柱子上方，通过'bottom'调整，显示第二种产品的销量
    ax.bar(shops, sales_product_2, color="blue", bottom=sales_product_1, label="Product_2")
    # 第三根柱子“堆积”在第二根柱子上方，通过'bottom'调整，显示第三种产品的销量
    ax.bar(shops, sales_product_3, color="green", 
           bottom=np.array(sales_product_2) + np.array(sales_product_1), label="Product_3")

    ax.set_title("Stacked Bar plot", fontsize=15)
    ax.set_xlabel("Shops")
    ax.set_ylabel("Product Sales")
    ax.legend()

    plt.show()

"""


# plot_uios(UIOs)




