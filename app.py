from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import threading
import json
import traceback
import os
import time
import uuid
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from biliUtils.bvConverter import BvConverter
from biliUtils.comment import Comment
from core.commentDB import MongoDBMix
from core.process import ProcessHandle
from server.client import ReqClient
from bili2text_handlers import bili2text_bp
from datetime import datetime
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point

# 添加视频转文本功能需要的导入
try:
    from bili2text.utils import download_video
    from bili2text.exAudio import process_audio_split
    import bili2text.speech2text as speech_to_text
    BILI2TEXT_AVAILABLE = True
except ImportError:
    print("bili2text模块导入失败，将使用本地实现")
    BILI2TEXT_AVAILABLE = False
    speech_to_text = None

app = Flask(__name__)
app.register_blueprint(bili2text_bp, url_prefix='/bili2text')

# 视频转文本任务状态
video_to_text_status = {
    "is_processing": False,
    "is_completed": False,
    "current_step": None,
    "progress": 0,
    "logs": [],
    "task_id": None,
    "result_file": None,
    "error": None
}

# 初始化MongoDB连接并添加异常处理
try:
    mongodb = MongoDBMix()
    # 测试连接
    mongodb.db.command('ping')
    print("MongoDB连接成功")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"MongoDB连接失败: {e}")
    mongodb = None

# 全局任务状态
task_status = {
    "is_running": False,
    "current_task": None,
    "progress": 0,
    "message": "",
    "total_main_comments": 0,
    "total_sub_comments": 0
}

# 视频转文本相关函数
def vtlog(message, state="INFO"):
    """添加视频转文本日志消息"""
    timestamp = time.strftime("%H:%M:%S")
    log_message = f"[{timestamp}][{state}] {message}"
    video_to_text_status["logs"].append(log_message)
    print(log_message)

    # 保持日志在合理长度
    if len(video_to_text_status["logs"]) > 100:
        video_to_text_status["logs"] = video_to_text_status["logs"][-100:]

def reset_video_to_text_status():
    """重置视频转文本任务状态"""
    video_to_text_status["is_processing"] = False
    video_to_text_status["is_completed"] = False
    video_to_text_status["current_step"] = None
    video_to_text_status["progress"] = 0
    video_to_text_status["logs"] = []
    video_to_text_status["task_id"] = None
    video_to_text_status["result_file"] = None
    video_to_text_status["error"] = None

def ensure_video_folders():
    """确保必要的文件夹存在"""
    for folder in ["bilibili_video", "outputs", "audio/conv", "audio/slice"]:
        os.makedirs(folder, exist_ok=True)
    vtlog(f"已创建必要文件夹")

def process_video_to_text(bv_number, model="small"):
    """处理视频转文本的主函数"""
    global video_to_text_status
    try:
        # 确保文件夹存在
        ensure_video_folders()

        # 下载视频
        video_to_text_status["current_step"] = "正在下载视频..."
        video_to_text_status["progress"] = 10
        vtlog("正在下载视频...")

        if BILI2TEXT_AVAILABLE:
            # 使用bili2text的download_video
            file_identifier = download_video(bv_number[2:] if bv_number.startswith("BV") else bv_number)
        else:
            # 使用handlers中的本地实现
            from bili2text_handlers import download_video_locally
            file_identifier = download_video_locally(bv_number)

        if not file_identifier:
            raise Exception("视频下载失败")

        vtlog(f"视频下载完成: {file_identifier}")

        # 分割音频
        video_to_text_status["current_step"] = "正在处理音频..."
        video_to_text_status["progress"] = 40
        vtlog("正在分割音频...")

        if BILI2TEXT_AVAILABLE:
            # 使用bili2text的音频处理
            folder_name = process_audio_split(file_identifier)
        else:
            # 使用handlers中的本地实现
            from bili2text_handlers import process_audio_locally
            folder_name = process_audio_locally(file_identifier)

        if not folder_name:
            raise Exception("音频处理失败")

        vtlog(f"音频处理完成，使用文件夹: {folder_name}")

        # 转换文本
        video_to_text_status["current_step"] = "正在转换文本（可能耗时较长）..."
        video_to_text_status["progress"] = 60
        vtlog("正在转换文本（可能耗时较长）...")

        if BILI2TEXT_AVAILABLE:
            # 确保加载了whisper模型
            if not hasattr(speech_to_text, 'whisper_model') or speech_to_text.whisper_model is None:
                vtlog(f"正在加载Whisper模型: {model}...")
                speech_to_text.load_whisper(model=model)

            # 使用bili2text的文本转换
            speech_to_text.run_analysis(
                folder_name,
                model=model,
                prompt=f"以下是普通话的句子。这是一个关于{file_identifier}的视频。"
            )
        else:
            # 使用handlers中的本地实现
            from bili2text_handlers import convert_to_text_locally
            convert_to_text_locally(folder_name, model, file_identifier)

        output_path = f"outputs/{folder_name}.txt"
        vtlog(f"转换完成! 结果保存在: {output_path}")

        # 任务完成
        video_to_text_status["progress"] = 100
        video_to_text_status["current_step"] = "处理完成"
        video_to_text_status["is_completed"] = True
        video_to_text_status["result_file"] = f"{folder_name}.txt"
        return True

    except Exception as e:
        vtlog(f"处理视频时出错: {str(e)}", "ERROR")
        video_to_text_status["error"] = str(e)
        return False
    finally:
        video_to_text_status["is_processing"] = False

def process_video_to_text_task(video_url, model="small"):
    """处理视频转文本任务的线程函数"""
    global video_to_text_status

    try:
        video_to_text_status["is_processing"] = True

        # 提取BV号
        import re
        pattern = r'BV[A-Za-z0-9]+'
        matches = re.findall(pattern, video_url)
        if not matches:
            video_to_text_status["error"] = "无效的视频链接"
            video_to_text_status["is_processing"] = False
            return

        bv_number = matches[0]
        vtlog(f"提取的BV号: {bv_number}")

        # 调用处理函数
        process_video_to_text(bv_number, model)

    except Exception as e:
        video_to_text_status["error"] = f"处理过程中发生错误: {str(e)}"
        vtlog(f"处理任务时发生错误: {str(e)}", "ERROR")
        video_to_text_status["is_processing"] = False

def process_video(bv):
    global task_status
    task_status["is_running"] = True
    task_status["current_task"] = bv
    task_status["message"] = "开始处理视频评论"
    task_status["progress"] = 0

    try:
        # 检查MongoDB连接
        if mongodb is None:
            task_status["message"] = "无法连接到MongoDB数据库，请检查配置"
            task_status["progress"] = 100
            task_status["is_running"] = False
            return

        # BV转AV
        bvConverter = BvConverter()
        oid = bvConverter.bv2av(bv)
        task_status["message"] = f"视频BV号 {bv} 转换为AV号 {oid}"
        task_status["progress"] = 10

        # 获取评论数量
        comment = Comment()
        count_data = comment.replyCount(oid)
        if count_data and 'data' in count_data and 'count' in count_data['data']:
            count = count_data['data']['count']
            task_status["message"] = f"视频共有 {count} 条评论"
        else:
            task_status["message"] = "无法获取评论数量，可能视频不存在或没有评论"
            task_status["is_running"] = False
            task_status["progress"] = 100
            return

        task_status["progress"] = 20

        # 获取主评论和子评论
        processHandle = ProcessHandle()

        task_status["message"] = "正在获取主评论..."
        processHandle.fetch_main_comments(oid)
        task_status["total_main_comments"] = len(processHandle.rpids_main)

        if len(processHandle.rpids_main) == 0:
            task_status["message"] = "未能获取到任何主评论，请检查网络或尝试其他视频"
            task_status["progress"] = 100
            task_status["is_running"] = False
            return

        task_status["message"] = f"已获取 {len(processHandle.rpids_main)} 条主评论"
        task_status["progress"] = 50

        # task_status["message"] = "正在获取子评论..."
        # processHandle.fetch_sub_comments(oid)
        # task_status["total_sub_comments"] = len(processHandle.rpids_sub)
        # task_status["message"] = f"已获取 {len(processHandle.rpids_sub)} 条子评论"
        # task_status["progress"] = 70

        # 添加评论到数据库中
        task_status["message"] = "正在将评论保存到数据库..."
        mongodb.insert_main_comments(processHandle.rpids_main)
        mongodb.insert_sub_comments(processHandle.rpids_sub)
        task_status["progress"] = 80

        # 获取数据库中的评论并请求nlp服务,然后更新结果
        task_status["message"] = "正在进行情感分析..."
        reqClient = ReqClient()

        all_main_comments = mongodb.get_main_comments_from_db()
        if all_main_comments:
            for i, comment in enumerate(all_main_comments):
                result = reqClient.req(comment)
                mongodb.update_main_comment_with_result(comment, result)
                # 更新进度
                progress_step = 10 / (len(all_main_comments) or 1)
                task_status["progress"] = 80 + progress_step * i
                task_status["message"] = f"正在分析主评论 ({i + 1}/{len(all_main_comments)})"
        else:
            task_status["message"] = "没有主评论数据进行分析"
            # task_status["progress"] = 90
            task_status["progress"] = 100

        # all_sub_comments = mongodb.get_sub_comments_from_db()
        # if all_sub_comments:
        #     for i, comment in enumerate(all_sub_comments):
        #         result = reqClient.req(comment)
        #         mongodb.update_sub_comment_with_result(comment, result)
        #         # 更新进度
        #         progress_step = 10 / (len(all_sub_comments) or 1)
        #         task_status["progress"] = 90 + progress_step * i
        #         task_status["message"] = f"正在分析子评论 ({i + 1}/{len(all_sub_comments)})"
        # else:
        #     task_status["message"] = "没有子评论数据进行分析"
        #     task_status["progress"] = 100

        task_status["progress"] = 100
        task_status["message"] = "处理完成！"
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"处理过程中出错: {e}\n{error_details}")
        task_status["message"] = f"处理过程中出错: {str(e)}"
    finally:
        task_status["is_running"] = False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/status')
def status():
    return jsonify(task_status)


@app.route('/analyze', methods=['POST'])
def analyze():
    if task_status["is_running"]:
        return jsonify({"success": False, "message": "已有任务正在进行中"}), 400

    data = request.get_json()
    bv = data.get('bv')

    if not bv:
        return jsonify({"success": False, "message": "缺少BV号"}), 400

    # 开始一个新线程处理数据
    threading.Thread(target=process_video, args=(bv,)).start()

    return jsonify({"success": True, "message": "分析任务已启动"})


@app.route('/get_comments')
def get_comments():
    """获取已分析的评论数据，用于前端展示"""
    try:
        # 检查MongoDB连接
        if mongodb is None:
            return jsonify({"error": "无法连接到MongoDB数据库，请检查配置"}), 500

        # 从数据库中获取已分析的评论
        main_comments = list(mongodb.db['main_comments'].find({}, {'_id': 0}))
        sub_comments = list(mongodb.db['sub_comments'].find({}, {'_id': 0}))

        # 构建结果
        result = {
            "main_comments": main_comments,
            "sub_comments": sub_comments
        }

        return jsonify(result)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"获取评论数据出错: {e}\n{error_details}")
        return jsonify({"error": str(e)}), 500


@app.route('/get_comments_by_bv')
def get_comments_by_bv():
    """根据BV号获取评论数据"""
    try:
        # 检查MongoDB连接
        if mongodb is None:
            return jsonify({"error": "无法连接到MongoDB数据库，请检查配置"}), 500

        # 获取BV号参数
        bv = request.args.get('bv', '')
        if not bv:
            return jsonify({"error": "缺少BV号参数"}), 400

        # BV转AV
        try:
            bvConverter = BvConverter()
            oid = bvConverter.bv2av(bv)
        except Exception as e:
            return jsonify({"error": f"BV号转换失败: {str(e)}"}), 400

        # 从数据库中获取对应视频的评论
        main_comments = list(mongodb.db['main_comments'].find({"oid": oid}, {'_id': 0}))
        sub_comments = list(mongodb.db['sub_comments'].find({"oid": oid}, {'_id': 0}))

        # 如果没有找到评论，返回错误信息
        if not main_comments and not sub_comments:
            return jsonify({"error": f"未找到视频 {bv} (AV{oid}) 的评论数据"}), 404

        # 构建结果
        result = {
            "main_comments": main_comments,
            "sub_comments": sub_comments,
            "bv": bv,
            "oid": oid
        }

        return jsonify(result)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"获取评论数据出错: {e}\n{error_details}")
        return jsonify({"error": str(e)}), 500


@app.route('/statistics')
def statistics():
    """获取情感分析统计数据"""
    try:
        # 检查MongoDB连接
        if mongodb is None:
            return jsonify({"error": "无法连接到MongoDB数据库，请检查配置"}), 500

        # 主评论统计
        main_positive = mongodb.db['main_comments'].count_documents({"result": "正向"})
        main_negative = mongodb.db['main_comments'].count_documents({"result": "负向"})
        main_neutral = mongodb.db['main_comments'].count_documents({"result": "未提及"})
        main_total = mongodb.db['main_comments'].count_documents({})

        # 子评论统计
        sub_positive = mongodb.db['sub_comments'].count_documents({"result": "正向"})
        sub_negative = mongodb.db['sub_comments'].count_documents({"result": "负向"})
        sub_neutral = mongodb.db['sub_comments'].count_documents({"result": "未提及"})
        sub_total = mongodb.db['sub_comments'].count_documents({})

        # 构建结果
        result = {
            "main_comments": {
                "positive": main_positive,
                "negative": main_negative,
                "neutral": main_neutral,
                "total": main_total
            },
            "sub_comments": {
                "positive": sub_positive,
                "negative": sub_negative,
                "neutral": sub_neutral,
                "total": sub_total
            },
            "total": {
                "positive": main_positive + sub_positive,
                "negative": main_negative + sub_negative,
                "neutral": main_neutral + sub_neutral,
                "total": main_total + sub_total
            }
        }

        return jsonify(result)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"获取统计数据出错: {e}\n{error_details}")
        return jsonify({"error": str(e)}), 500


@app.route('/statistics_by_bv')
def statistics_by_bv():
    """根据BV号获取情感分析统计数据"""
    try:
        # 检查MongoDB连接
        if mongodb is None:
            return jsonify({"error": "无法连接到MongoDB数据库，请检查配置"}), 500

        # 获取BV号参数
        bv = request.args.get('bv', '')
        if not bv:
            return jsonify({"error": "缺少BV号参数"}), 400

        # BV转AV
        try:
            bvConverter = BvConverter()
            oid = bvConverter.bv2av(bv)
        except Exception as e:
            return jsonify({"error": f"BV号转换失败: {str(e)}"}), 400

        # 主评论统计
        main_positive = mongodb.db['main_comments'].count_documents({"oid": oid, "result": "正向"})
        main_negative = mongodb.db['main_comments'].count_documents({"oid": oid, "result": "负向"})
        main_neutral = mongodb.db['main_comments'].count_documents({"oid": oid, "result": "未提及"})
        main_total = mongodb.db['main_comments'].count_documents({"oid": oid})

        # 子评论统计
        sub_positive = mongodb.db['sub_comments'].count_documents({"oid": oid, "result": "正向"})
        sub_negative = mongodb.db['sub_comments'].count_documents({"oid": oid, "result": "负向"})
        sub_neutral = mongodb.db['sub_comments'].count_documents({"oid": oid, "result": "未提及"})
        sub_total = mongodb.db['sub_comments'].count_documents({"oid": oid})

        # 如果没有找到评论，返回错误信息
        if main_total == 0 and sub_total == 0:
            return jsonify({"error": f"未找到视频 {bv} (AV{oid}) 的评论数据"}), 404

        # 构建结果
        result = {
            "main_comments": {
                "positive": main_positive,
                "negative": main_negative,
                "neutral": main_neutral,
                "total": main_total
            },
            "sub_comments": {
                "positive": sub_positive,
                "negative": sub_negative,
                "neutral": sub_neutral,
                "total": sub_total
            },
            "total": {
                "positive": main_positive + sub_positive,
                "negative": main_negative + sub_negative,
                "neutral": main_neutral + sub_neutral,
                "total": main_total + sub_total
            },
            "bv": bv,
            "oid": oid
        }

        return jsonify(result)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"获取统计数据出错: {e}\n{error_details}")
        return jsonify({"error": str(e)}), 500


# 视频转文本功能的路由
@app.route('/video_to_text')
def video_to_text():
    """视频转文本页面"""
    return render_template('video_to_text.html')

@app.route('/video_to_text/process', methods=['POST'])
def process_video_text():
    """开始处理视频转文本"""
    if video_to_text_status["is_processing"]:
        return jsonify({"success": False, "message": "已有任务正在处理中"})

    try:
        data = request.get_json()
        video_url = data.get('video_url')
        model = data.get('model', 'small')

        if not video_url:
            return jsonify({"success": False, "message": "缺少视频链接"})

        # 重置状态
        reset_video_to_text_status()

        # 生成任务ID
        task_id = str(uuid.uuid4())
        video_to_text_status["task_id"] = task_id

        # 启动处理线程
        thread = threading.Thread(target=process_video_to_text_task, args=(video_url, model))
        thread.start()

        return jsonify({
            "success": True,
            "message": "任务已启动",
            "task_id": task_id
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"启动任务失败: {str(e)}"})

@app.route('/video_to_text/status')
def video_to_text_status_route():
    """获取当前视频转文本任务状态"""
    return jsonify(video_to_text_status)

@app.route('/video_to_text/result/<filename>')
def video_to_text_result(filename):
    """获取视频转文本的结果"""
    try:
        return send_from_directory('outputs', filename)
    except Exception as e:
        return f"获取结果失败: {str(e)}", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
