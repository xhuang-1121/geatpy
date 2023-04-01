# -*- coding: utf-8 -*-
import geatpy as ea # 导入geatpy库
from sys import path as paths
from os import path
paths.append(path.split(path.split(path.realpath(__file__))[0])[0])

class soea_DE_targetToBest_1_bin_templet(ea.SoeaAlgorithm):
    
    """
soea_DE_targetToBest_1_bin_templet : class - 差分进化DE/target-to-best/1/bin算法模板

算法描述:
    本模板实现的是经典的DE/target-to-best/1/bin单目标差分进化算法。
    为了实现矩阵化计算，本模板采用打乱个体顺序来代替随机选择差分向量。算法流程如下：
    1) 初始化候选解种群。
    2) 若满足停止条件则停止，否则继续执行。
    3) 对当前种群进行统计分析，比如记录其最优个体、平均适应度等等。
    4) 采用target-to-best的方法选择差分变异的基向量，对当前种群进行差分变异，得到变异个体。
    5) 将当前种群和变异个体合并，采用二项式分布交叉方法得到试验种群。
    6) 在当前种群和实验种群之间采用一对一生存者选择方法得到新一代种群。
    7) 回到第2步。

模板使用注意:
    本模板调用的目标函数形如：aimFunc(pop), 
    其中pop为Population类的对象，代表一个种群，
    pop对象的Phen属性（即种群染色体的表现型）等价于种群所有个体的决策变量组成的矩阵，
    该函数根据该Phen计算得到种群所有个体的目标函数值组成的矩阵，并将其赋值给pop对象的ObjV属性。
    若有约束条件，则在计算违反约束程度矩阵CV后赋值给pop对象的CV属性（详见Geatpy数据结构）。
    该函数不返回任何的返回值，求得的目标函数值保存在种群对象的ObjV属性中，
                          违反约束程度矩阵保存在种群对象的CV属性中。
    例如：population为一个种群对象，则调用aimFunc(population)即可完成目标函数值的计算，
         此时可通过population.ObjV得到求得的目标函数值，population.CV得到违反约束程度矩阵。
    若不符合上述规范，则请修改算法模板或自定义新算法模板。

参考文献:
    [1] Price, K.V., Storn, R.N. and Lampinen, J.A.. Differential Evolution: 
        A Practical Approach to Global Optimization. : Springer, 2005.

"""
    
    def __init__(self, problem, population):
        ea.SoeaAlgorithm.__init__(self, problem, population) # 先调用父类构造方法
        if str(type(population)) != "<class 'Population.Population'>":
            raise RuntimeError('传入的种群对象必须为Population类型')
        self.name = 'DE/rand/1/bin'
        if population.Encoding != 'RI':
            raise RuntimeError('编码方式必须为''RI''.')
        self.mutOper = ea.Mutde(F = 0.5) # 生成差分变异算子对象
        self.recOper = ea.Xovbd(XOVR = 0.5, Half = True) # 生成二项式分布交叉算子对象，这里的XOVR即为DE中的Cr
        self.k = 0.5 # target-to-best中的参数k
        
    def run(self, prophetPop = None): # prophetPop为先知种群（即包含先验知识的种群）
        #==========================初始化配置===========================
        population = self.population
        NIND = population.sizes
        self.initialization() # 初始化算法模板的一些动态参数
        #===========================准备进化============================
        if population.Chrom is None:
            population.initChrom(NIND) # 初始化种群染色体矩阵（内含染色体解码，详见Population类的源码）
        else:
            population.Phen = population.decoding() # 染色体解码
        self.problem.aimFunc(population) # 计算种群的目标函数值
        self.evalsNum = population.sizes # 记录评价次数
        # 插入先验知识（注意：这里不会对先知种群prophetPop的合法性进行检查，故应确保prophetPop是一个种群类且拥有合法的Chrom、ObjV、Phen等属性）
        if prophetPop is not None:
            population = (prophetPop + population)[:NIND] # 插入先知种群
        population.FitnV = ea.scaling(self.problem.maxormins * population.ObjV, population.CV) # 计算适应度
        #===========================开始进化============================
        while self.terminated(population) == False:
            # 进行差分进化操作
            r0 = ea.selecting('ecs', population.FitnV, NIND)
            Xr0 = population.Chrom + self.k * (population.Chrom[r0, :] - population.Chrom) # 根据target-to-best的方法得到基向量矩阵
            experimentPop = population.copy() # 存储试验个体
            experimentPop.Chrom = self.mutOper.do(experimentPop.Encoding, experimentPop.Chrom, experimentPop.Field, [Xr0]) # 变异
            tempPop = population + experimentPop # 当代种群个体与变异个体进行合并（为的是后面用于重组）
            experimentPop.Chrom = self.recOper.do(tempPop.Chrom) # 重组
            # 求进化后个体的目标函数值
            experimentPop.Phen = experimentPop.decoding() # 染色体解码
            self.problem.aimFunc(experimentPop) # 计算目标函数值
            self.evalsNum += experimentPop.sizes # 更新评价次数
            tempPop = population + experimentPop # 临时合并，以调用otos进行一对一生存者选择
            tempPop.FitnV = ea.scaling(self.problem.maxormins * tempPop.ObjV, tempPop.CV) # 计算适应度
            population = tempPop[ea.selecting('otos', tempPop.FitnV, NIND)] # 采用One-to-One Survivor选择，产生新一代种群
        
        return self.finishing(population) # 调用finishing完成后续工作并返回结果
