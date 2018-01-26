# Robo-Advisor

#以下为模型演算和util部分


**robolib.py 主要的函数文件，放置各种通用函数**
**iolib.py io操作（读写文件等）的主要库函数**
single_opt.py  主要功能是对某一种特定的用户产品组合进行优化以及输出图示使用
user_type_all.py  根据输入类别计算所有配置组合的年化收益率
poc_statistics.py 统计poc结果的函数（已废弃）
poc_sta_re 对poc中的历史回测部分进行验证的模块
poc_micro_sta.py 对poc中厂家给出的配置进行微观分析的模块，目前实现了相关系数分析
poc_sta_real.py 对poc中每次给出的模型进行实测验证的模块
**poc_sta_online.py 对poc中每次给出的模型进行实测验证的模块**

#以下为自行实现的模型优化部分


**funds_selection.py 基金的聚类和选择模块**
**mpt.py 马科维茨有效前沿模型函数库**
poc_zs.py 根据马科维茨有效前沿理论以及前述基金聚类结果进行动态调仓、以及用户个性化比例配置的模块
**poc_zsmk_seg.py 最新的生成自有模型的文件**

#以下为文件夹说明


history_data 保存历史的行情数据、策略配置数据、指数数据、用户数据等计算所需数据的文件夹
resutl 保存返回的结果文件的文件夹

