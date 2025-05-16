# BiliCommentNLP - 哔哩哔哩评论情感分析系统

这是一个用于抓取B站视频评论并进行情感分析的系统，通过Web界面可视化展示分析结果。

## 功能特点

- 通过BV号抓取视频评论（主评论和子评论）
- 使用NLP模型进行情感分析
- 数据持久化存储到MongoDB
- 美观的Web界面展示分析结果
- 实时进度显示和状态更新
- 评论数据可视化和统计

## 系统要求

- Python 3.7+
- MongoDB
- PaddleNLP

## 安装与配置

1. 克隆或下载代码到本地
2. 安装依赖:

```bash
pip install flask pymongo paddlenlp requests
```

3. 确保MongoDB服务已启动
4. 启动NLP服务:

```bash
paddlenlp server server:app --workers 1 --host 0.0.0.0 --port 8189
```

## 使用方法

1. 启动Web服务:

```bash
python app.py
```

2. 在浏览器中访问 `http://localhost:5000`
3. 在输入框中输入B站视频的BV号（例如: BV1BfGqzDE59）
4. 点击"开始分析"按钮
5. 系统会自动抓取评论数据，并进行情感分析
6. 分析结果将在Web界面上直观展示

## 系统架构

- `app.py`: Flask Web服务和主要控制逻辑
- `biliUtils/`: B站API工具包
- `core/`: 核心处理功能
- `server/`: NLP服务相关代码
- `templates/`: Web前端HTML模板
- `static/`: 静态资源文件

## 注意事项

- 请合理使用，避免频繁请求对B站服务器造成压力
- 情感分析结果仅供参考，准确度取决于NLP模型的质量
- 确保MongoDB和NLP服务正常运行，否则系统将无法正常工作

## 许可证

MIT 