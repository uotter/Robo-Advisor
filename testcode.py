import tushare as ts
import pandas as pd
import robolib as rl
import datetime
startday_str = "2017-01-01"
endday_str = "2017-08-31"
startday = datetime.datetime.strptime(startday_str, '%Y-%m-%d')
endday = datetime.datetime.strptime(endday_str, '%Y-%m-%d')
# shibor_path = r"F:\Code\Robo-Advisor\history_data\Shibor.csv"
#
# shibor = pd.read_csv(shibor_path).set_index("date")
#
# sort_date_shibor = (rl.fillDepsoit(startday_str,endday_str,shibor,"1W")).sort_index()
#
# print(sort_date_shibor)

# test1 = ts.get_latest_news() #默认获取最近80条新闻数据，只提供新闻类型、链接和标题
# test2 = ts.get_latest_news(top=5,show_content=True) #显示最新5条新闻，并打印出新闻内容

test3 = ts.get_concept_classified()
# print(test1)
# print(test2)
print(test3)