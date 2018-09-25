# order问题的描述
# 优化目标：找出对order最优的plant和生产时间week
#

# 最终要求的解：week/plant 的ID
# 输入： (delivery date/leading time/plant volume)
#
#

from NSGA import nsga2
import random

NaN = 99999
Hmin = 0.5


# col: week
# row: plant
def read_col_data(filename, datatype=int):
    path = 'data/' + filename + '.txt'
    f = open(path, 'r')
    tag = f.readline().strip('\n').split(' ')
    res = {}
    for t in tag:
        res[t] = []
    for l in f.readlines():
        line = l.strip('\n').split(' ')
        for i in range(len(line)):
            res[tag[i]].append(datatype(line[i]))
    return res


def read_data(filename, datatype=int):
    path = 'data/' + filename + '.txt'
    f = open(path, 'r')
    line = f.readline().strip('\n').split(' ')
    tp = []
    for l in f.readlines():
        line = l.strip('\n').split(' ')
        try:
            line = [datatype(k) for k in line]
        except:
            print(line)
        tp.append(line)
    return tp


def read_data_f(filename, datatype=int):
    # exmp: residual_capacity:
    filename += '_f%d'
    res = {}
    for i in range(1, 11):
        dt = read_data(filename % i, datatype=datatype)
        res[i] = dt
    return res


class orderq:
    def __init__(self):
        self.plant_num = 20
        self.family_num = 10
        self.week_max = 20
        self.plant_volume_mat = {}
        self.plant_time_mat = {}
        self.cur_order = {}  # id - {'volume','family','date','item'}
        # ===data:
        self.order = read_col_data('order')
        self.lead_time = read_data('lead_time')
        self.logistic_cost = read_data('logistic_cost')
        self.production_cost = read_data('production_cost')
        self.production_strategy = read_data('production_strategy')
        self.target_price_contribution = read_data('target_price_contribution')

        self.hit_ratio = read_data_f('hit_ratio', datatype=float)
        self.target_capacity = read_data_f('target_capacity')
        self.residual_capacity = read_data_f('residual_capacity')

    def order_volume(self, f=None):
        res = 0
        order = self.order
        family = order['Product_Family']
        volume = order['Volume']
        for i in range(len(family)):
            if f is None or family[i] == f:
                res += volume[i]
        return res

    # 带权规格和，fun为二维矩阵 格式为fun[p][fid]
    def order_volue_pow(self, p, f, fun):
        res = 0
        order = self.order
        family = order['Product_Family']
        volume = order['Volume']
        for i in range(len(family)):
            if f is None or family[i] == f:
                fid = family[i] - 1
                res += volume[i] * fun[p][fid]
        return res

    # Rp,w,f
    def residual_production(self, p, w, f):
        return self.residual_capacity[f][p][w] - self.order_volume(f)

    # M p,f
    def margin_per(self, p, f):
        Clog = self.logistic_cost[p][0] * self.order_volume()
        Cprd = self.order_volue_pow(p, f, self.production_cost)
        Pi = self.order_volue_pow(p, f, self.target_price_contribution)
        return Pi - (Clog + Cprd)

    def get_hit_ratio(self, p, item, price):
        family = self.order['Product_Family']
        f = family[item]
        fid = f - 1
        #price = self.production_cost[p][fid]
        hr = self.hit_ratio[f]
        for i in range(len(hr)):
            l = hr[i]
            if price < l[2]:
                return l[3]
        return 0

    # 限制函数: 符合限制返回true
    def constraint(self, x):
        p, w = x[0], x[1]
        if p <= 0 or p > self.plant_num:
            return False
        if w <= 0 or w > self.week_max:
            return False
        Lptot = 0
        family = set(self.order['Product_Family'])
        for f in family:
            fid = f - 1
            pid = p - 1
            t = self.lead_time[pid][fid]
            if t > Lptot:
                Lptot = t
        delivertime = self.order['Delivery_Date'][0]
        if w > delivertime - Lptot:
            return False
        return True

    def PTV(self, x):
        p, w = x[0] - 1, x[1] - 1  # 下标变换
        res = 0
        family = set(self.order['Product_Family'])
        for f in family:
            r = self.residual_production(p, w, f)
            rt = self.target_capacity[f][p][w]
            res += max(r - rt, 0)
        return res

    def Delay(self, x):
        p, w = x[0] - 1, x[1] - 1
        Lptot = 0
        family = set(self.order['Product_Family'])
        for f in family:
            fid = f - 1
            t = self.lead_time[p][fid]
            if t > Lptot:
                Lptot = t
        return max(w + Lptot - self.order['Delivery_Date'][0], 0)

    def RF(self, x):
        p, w = x[0] - 1, x[1] - 1
        family = set(self.order['Product_Family'])
        mx = 0
        for f in family:
            fid = f - 1
            r = self.residual_production(p, w, f)
            fpf = self.production_strategy[p][fid]
            temp = r * fpf
            if temp > mx:
                mx = temp
        return mx

    def MV(self, x):
        p, w = x[0] - 1, x[1] - 1
        family = set(self.order['Product_Family'])
        res = 0
        for f in family:
            res += max(self.margin_per(p, f), 0)
        return res

    def HR(self, x):
        p, w = x[0] - 1, x[1] - 1
        price = x[2]
        family = set(self.order['Product_Family'])
        res = 0
        for item in range(len(family)):
            temp = max(Hmin - self.get_hit_ratio(p, item, price), 0)
            if temp > res:
                res = temp
        return res

    def solve(self):
        pass


if __name__ == '__main__':
    q = orderq()
    ga = nsga2()
    ga.init_params(f=[q.PTV, q.Delay, q.RF, q.MV, q.HR],  # 目标函数
                   df=[(1, 21), (1, 21), (200, 1000)],  # 定义域
                   cf=[q.constraint])  # 约束函数
    p = random.sample([i for i in range(1, 21)], 20)
    w = random.sample([i for i in range(1, 21)], 20)
    price = random.sample([i for i in range(200, 1000)], 20)
    I = []  # 初始种群
    for i in zip(p, w, price):
        I.append(i)
    print(I)
    print('最优解集：', ga.solve(I, recurnum=40))
