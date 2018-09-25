import random

NaN = 999999


class nsga2:
    def __init__(self, dir='min'):
        if dir == 'min':
            self.dir = -1
        else:
            self.dir = 1
        self.crowd = {}

        # 交叉率、变异率
        self.cross_rate = 0.25
        self.mute_rate = 0.001

    # 设置 目标函数 定义域 约束函数
    def init_params(self, f, df, cf=[], k=10):
        self.objfun = f
        self.funrange = {}
        self.consfun = cf
        self.xdomain = df
        self.k = k
        '''
        for i in range(len(df)):
            mx = 0
            mi = NaN
            for v in range(df[i][0], df[i][1]):
                y = f[i](v)
                if y < mi:
                    mi = y
                if y > mx:
                    mx = y
            self.funrange[f[i]] = (mi, mx)
        '''

    def is_constraint(self, x):
        for f in self.consfun:
            if f(x) is False:
                return False
        return True

    def is_dominate(self, s, t):
        # print('#calculate',s,'|',t)
        for f in self.objfun:
            a = self.dir * f(s)
            b = self.dir * f(t)
            # print('\t\t',f.__name__,a,b)
            if a > b:  # advantage
                continue
            else:
                return False
        print('\t', s, 'dominate', t)
        return True

    # 支配排序 fast nondominate sort
    def nsort(self, gruopx):
        F = []
        P = gruopx
        n = {}
        S = {}
        F1 = []
        self.rankf = {}
        xrank = {}
        for p in P:
            print(p)
            S[p] = []
            n[p] = 0
            for q in P:
                if p is q or p == q:
                    continue
                if self.is_dominate(p, q):
                    S[p].append(q)
                    xrank[p] = 0
                else:
                    n[p] += 1
            print('\tnp: ', n[p])
            if n[p] == 0:
                F1.append(p)
        while len(F1) == 0:
            for p in n:
                if n[p] > 0:
                    n[p] -= 1
                if n[p] == 0:
                    F1.append(p)
                    xrank[p] = 0
        F.append(F1)
        sz = len(F1)
        i = 0
        while sz < len(gruopx):
            print('sz:', sz)
            print('----F----: ', F)
            Q = []
            for p in F[i]:
                for q in S[p]:
                    if p == q:
                        continue
                    n[q] -= 1
                    print('\t', n[q])
                    if n[q] == 0:
                        xrank[q] = i + 1
                        Q.append(q)
            while len(Q) == 0:
                for p in n:
                    if n[p] > 0:
                        n[p] -= 1
                    if n[p] == 0:
                        xrank[p] = i + 1
                        Q.append(p)
            F.append(Q)
            print('Q:', Q)
            sz += len(Q)
            i += 1
        self.rankf = xrank
        return F

    # 密度距离估计 传入可行解集
    def crowding_distance_assignment(self, I):
        distance = {}
        print('calculate distance:', I)
        for i in I:
            distance[i] = 0
        for f in self.objfun:
            tempx = sorted(I, key=lambda x: f(x))
            # print('tempx/I:', tempx, I)
            distance[tempx[0]] = NaN
            distance[tempx[-1]] = NaN
            for i in range(1, len(tempx) - 1):
                if distance[tempx[i]] != NaN:
                    # frange = self.funrange[f]
                    distance[tempx[i]] += (f(tempx[i - 1]) - f(tempx[i + 1]))  # / (frange[1] - frange[0])
        for d in distance:
            self.crowd[d] = distance[d]
            print('\tcrowd', d, distance[d])
        return distance

    # 排挤比较算子 : 判断  i < j ?
    def comparsion(self, i, j):
        if self.rankf[i] < self.rankf[j]:
            return True
        elif self.rankf[i] == self.rankf[j]:
            if self.crowd[i] > self.rankf[j]:
                return True
        return False

    def cal_cmp(self, x):
        try:
            ret = (NaN + 1) * self.rankf[x] + self.crowd[x]
        except:
            print(x)
            print(x in self.rankf, x in self.crowd)
            print(self.rankf)
            print(self.crowd)
            input()
            return 0
        return ret

    # 锦标赛选择
    def tournament_selection(self, I):
        res = []
        smp = random.sample(I, max(10, int(len(I) / 2)))

    # 遗传变异
    def genetic_mutation(self, I):
        x1 = I[0]
        x2 = I[1]
        res = list(x1)
        rdm = random.random()
        if rdm >= self.cross_rate:
            return res
        for i in range(len(res)):
            rdm = random.random()
            if rdm < self.cross_rate:
                res[i] = x2[i]
            rdm = random.random()
            if rdm < self.mute_rate:
                x_1 = self.xdomain[i][0]
                x_2 = self.xdomain[i][1]
                res[i] = random.sample([j for j in range(x_1, x_2)], 1)[0]
        return tuple(res)

    # genetic transform 选择父本进行交叉变异产生新一代
    def create_new_generation(self, I):
        res = []
        # I.sort(key=lambda x:(NaN+1)*self.rankf[x]+self.crowd[x],reverse=True)
        while len(res) < len(I):
            chos = random.sample(I, min(len(I), self.k))
            chos.sort(key=lambda x: self.cal_cmp(x))
            newgen = self.genetic_mutation(chos)
            newgen = tuple(newgen)
            if newgen not in res and self.is_constraint(newgen):
                res.append(newgen)
        print("new gen", len(res), ":", res)
        return res

    # 迭代
    def solve(self, I, recurnum=40):
        N = len(I)
        F = self.nsort(I)
        P = []
        for f in F:
            self.crowding_distance_assignment(f)
            P += f
        P = I
        print('start:', 'I:', I, 'P:', P)
        while recurnum > 0:
            print('#', recurnum)
            recurnum -= 1
            # 二进制锦标赛 + 遗传变异 产生新个体Q
            print('old gen', len(P), ':', P)
            Q = self.create_new_generation(P)
            R = P + Q
            F = self.nsort(R)
            print("nsort", len(F), ":", F)
            P = []
            # 排挤算法选出N个精英P:
            for f in F:
                if len(f) == 0:
                    continue
                self.crowding_distance_assignment(f)
                if len(P) + len(f) <= N:
                    P += f
                else:
                    P += f[0:N - len(f)]
                    break
            print('\t', "P", P)
        return P


### nsga baseline: 测试nsga2的基准问题 经测试收敛

def f1(x):
    x1 = x[0]
    x2 = x[1]
    return x1 - x2


def f2(x):
    x1 = x[0]
    x2 = x[1]
    return 2 * x1 - x2


if __name__ == '__main__':
    f = [f1, f2]
    group = [(0, 1), (1, 1), (0, 3)]

    ag = nsga2()

    # give funcs and x domains
    ag.init_params(f, [(0, 10), (0, 10)])

    print(ag.solve(group))
