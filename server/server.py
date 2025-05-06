from paddlenlp import SimpleServer, Taskflow
# 启动命令 paddlenlp server server:app --workers 1 --host 0.0.0.0 --port 8189

schema = [{"评价维度": ["观点词", "情感倾向[正向,负向,未提及]"]}]
schema2 = "情感倾向[正向,负向,未提及]"
senta = Taskflow("sentiment_analysis", schema=schema2, model="uie-senta-base")
app = SimpleServer()
app.register_taskflow("taskflow/senta", senta)

