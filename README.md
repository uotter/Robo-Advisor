# Robo-Advisor

robolib.py 主要的函数文件，放置各种函数
single_opt.py  主要功能是对某一种特定的用户产品组合进行优化以及输出图示使用
user_type_all.py  根据输入类别计算所有配置组合的年化收益率
poc_statistics.py 统计poc结果的函数（已废弃）
poc_sta_re 对poc中的历史回测部分进行验证的模块
poc_micro_sta.py 对poc中厂家给出的配置进行微观分析的模块，目前实现了相关系数分析
poc_sta_real 对poc中每次给出的模型进行实测验证的模块

#以下为自行实现的模型优化部分
funds_selection.py 基金的聚类和选择模块
mpt.py 马科维茨有效前沿模型函数库
poc_zs.py 根据马科维茨有效前沿理论以及前述基金聚类结果进行动态调仓、以及用户个性化比例配置的模块

