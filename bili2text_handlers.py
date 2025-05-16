import os
import time
import re
import uuid
import threading
import subprocess
import json
from flask import Blueprint, request, jsonify, send_from_directory, render_template

# 模块导入 
try:
    import sys
    from bili2text.utils import download_video
    from bili2text.exAudio import convert_flv_to_mp3, split_mp3, process_audio_split
    import bili2text.speech2text as speech_to_text

    BILI2TEXT_AVAILABLE = True
except ImportError:
    print("bili2text模块导入失败，将使用本地实现")
    BILI2TEXT_AVAILABLE = False
    speech_to_text = None

# 创建Blueprint
bili2text_bp = Blueprint('bili2text', __name__)

# 全局变量
TASK_STATUS = {
    "is_processing": False,
    "is_completed": False,
    "current_step": None,
    "progress": 0,
    "logs": [],
    "task_id": None,
    "result_file": None,
    "error": None
}


def log(message, state="INFO"):
    """添加日志消息"""
    timestamp = time.strftime("%H:%M:%S")
    log_message = f"[{timestamp}][{state}] {message}"
    TASK_STATUS["logs"].append(log_message)
    print(log_message)

    # 保持日志在合理长度
    if len(TASK_STATUS["logs"]) > 100:
        TASK_STATUS["logs"] = TASK_STATUS["logs"][-100:]


def reset_task_status():
    """重置任务状态"""
    TASK_STATUS["is_processing"] = False
    TASK_STATUS["is_completed"] = False
    TASK_STATUS["current_step"] = None
    TASK_STATUS["progress"] = 0
    TASK_STATUS["logs"] = []
    TASK_STATUS["task_id"] = None
    TASK_STATUS["result_file"] = None
    TASK_STATUS["error"] = None


def ensure_folders():
    """确保必要的文件夹存在"""
    for folder in ["bilibili_video", "outputs", "audio/conv", "audio/slice"]:
        os.makedirs(folder, exist_ok=True)
    log(f"已创建必要文件夹")


def extract_bv_number(video_link):
    """从视频链接提取BV号"""
    pattern = r'BV[A-Za-z0-9]+'
    matches = re.findall(pattern, video_link)
    if not matches:
        log("无效的视频链接，未找到BV号", "ERROR")
        return None

    bv_number = matches[0]
    log(f"提取的BV号: {bv_number}")
    return bv_number


def process_video(bv_number, model="small"):
    """处理视频的主函数，遵循window.py的逻辑"""
    global TASK_STATUS
    try:
        # 确保文件夹存在
        ensure_folders()

        # 下载视频
        TASK_STATUS["current_step"] = "正在下载视频..."
        TASK_STATUS["progress"] = 10
        log("正在下载视频...")

        if BILI2TEXT_AVAILABLE:
            # 使用bili2text的download_video
            file_identifier = download_video(bv_number[2:] if bv_number.startswith("BV") else bv_number)
        else:
            # 本地实现
            file_identifier = download_video_locally(bv_number)

        if not file_identifier:
            raise Exception("视频下载失败")

        log(f"视频下载完成: {file_identifier}")

        # 分割音频
        TASK_STATUS["current_step"] = "正在处理音频..."
        TASK_STATUS["progress"] = 40
        log("正在分割音频...")

        if BILI2TEXT_AVAILABLE:
            # 使用bili2text的音频处理
            folder_name = process_audio_split(file_identifier)
        else:
            # 本地实现
            folder_name = process_audio_locally(file_identifier)

        if not folder_name:
            raise Exception("音频处理失败")

        log(f"音频处理完成，使用文件夹: {folder_name}")

        # 转换文本
        TASK_STATUS["current_step"] = "正在转换文本（可能耗时较长）..."
        TASK_STATUS["progress"] = 60
        log("正在转换文本（可能耗时较长）...")

        if BILI2TEXT_AVAILABLE:
            # 确保加载了whisper模型
            if not hasattr(speech_to_text, 'whisper_model') or speech_to_text.whisper_model is None:
                log(f"正在加载Whisper模型: {model}...")
                speech_to_text.load_whisper(model=model)

            # 使用bili2text的文本转换
            speech_to_text.run_analysis(
                folder_name,
                model=model,
                prompt=f"以下是普通话的句子。这是一个关于{file_identifier}的视频。"
            )
        else:
            # 本地实现
            convert_to_text_locally(folder_name, model, file_identifier)

        output_path = f"outputs/{folder_name}.txt"
        log(f"转换完成! 结果保存在: {output_path}")

        # 任务完成
        TASK_STATUS["progress"] = 100
        TASK_STATUS["current_step"] = "处理完成"
        TASK_STATUS["is_completed"] = True
        TASK_STATUS["result_file"] = f"{folder_name}.txt"
        return True

    except Exception as e:
        log(f"处理视频时出错: {str(e)}", "ERROR")
        TASK_STATUS["error"] = str(e)
        return False
    finally:
        TASK_STATUS["is_processing"] = False


def download_video_locally(bv_number):
    """本地实现的视频下载功能"""
    try:
        video_url = f"https://www.bilibili.com/video/{bv_number}"
        ensure_folders()
        output_dir = "bilibili_video"

        log(f"使用you-get下载视频: {video_url}")
        try:
            result = subprocess.run(["you-get", "-o", output_dir, video_url],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                log(f"下载失败: {result.stderr}", "ERROR")
                return None

            log(f"视频已成功下载到目录: {output_dir}")

            # 重命名下载的视频文件为BV号
            video_files = [f for f in os.listdir(output_dir) if f.endswith(".mp4")]
            if video_files:
                latest_file = max(video_files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
                old_path = os.path.join(output_dir, latest_file)
                new_path = os.path.join(output_dir, f"{bv_number}.mp4")

                # 如果文件已存在，先删除
                if os.path.exists(new_path):
                    os.remove(new_path)

                os.rename(old_path, new_path)
                log(f"视频文件已重命名: {new_path}")

                # 删除可能的XML文件
                for xml_file in [f for f in os.listdir(output_dir) if f.endswith(".xml")]:
                    os.remove(os.path.join(output_dir, xml_file))

                return bv_number
            else:
                log("未找到下载的视频文件", "ERROR")
                return None
        except Exception as e:
            log(f"下载过程中出错: {str(e)}", "ERROR")
            return None
    except Exception as e:
        log(f"下载视频时出错: {str(e)}", "ERROR")
        return None


def process_audio_locally(file_identifier):
    """本地实现的音频处理功能"""
    try:
        from moviepy.editor import VideoFileClip
        from pydub import AudioSegment

        # 生成唯一文件夹名
        folder_name = time.strftime('%Y%m%d%H%M%S')
        log(f"创建音频文件夹: {folder_name}")

        # 提取视频中的音频
        video_path = f"bilibili_video/{file_identifier}.mp4"
        audio_path = f"audio/conv/{folder_name}.mp3"

        log(f"从视频中提取音频: {video_path}")
        os.makedirs("audio/conv", exist_ok=True)

        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
        log(f"音频提取完成: {audio_path}")

        # 分割音频
        audio = AudioSegment.from_mp3(audio_path)
        slice_length = 45000  # 45秒，与bili2text保持一致
        total_slices = len(audio) // slice_length

        target_dir = f"audio/slice/{folder_name}"
        os.makedirs(target_dir, exist_ok=True)

        log(f"将音频分割为 {total_slices} 个片段...")
        for i in range(total_slices):
            start = i * slice_length
            end = start + slice_length
            slice_audio = audio[start:end]
            slice_path = os.path.join(target_dir, f"{i + 1}.mp3")
            slice_audio.export(slice_path, format="mp3")
            log(f"音频片段 {i + 1}/{total_slices} 已保存")

        # 如果有剩余部分
        if len(audio) % slice_length > 0:
            start = total_slices * slice_length
            end = len(audio)
            slice_audio = audio[start:end]
            slice_path = os.path.join(target_dir, f"{total_slices + 1}.mp3")
            slice_audio.export(slice_path, format="mp3")
            log(f"最后一个音频片段已保存")

        return folder_name
    except Exception as e:
        log(f"处理音频时出错: {str(e)}", "ERROR")
        return None


def convert_to_text_locally(folder_name, model="small", file_identifier="unknown"):
    """本地实现的音频转文本功能"""
    try:
        import whisper

        log(f"正在加载Whisper模型 ({model})...")
        device = "cuda" if whisper.torch.cuda.is_available() else "cpu"
        whisper_model = whisper.load_model(model, device=device)
        log(f"Whisper模型加载成功! 使用设备: {device}")

        # 创建输出文件夹
        os.makedirs("outputs", exist_ok=True)
        output_file = f"outputs/{folder_name}.txt"

        # 读取列表中的音频文件
        audio_dir = f"audio/slice/{folder_name}"
        audio_list = sorted([f for f in os.listdir(audio_dir) if f.endswith('.mp3')],
                            key=lambda x: int(x.split('.')[0]))

        log(f"开始转换 {len(audio_list)} 个音频文件...")

        # 转换并写入文件
        with open(output_file, "w", encoding="utf-8") as f:
            for i, audio_file in enumerate(audio_list):
                audio_path = os.path.join(audio_dir, audio_file)
                log(f"正在转换第 {i + 1}/{len(audio_list)} 个音频... {audio_file}")

                # 更新进度
                progress = int(60 + (i / len(audio_list)) * 40)
                TASK_STATUS["progress"] = min(progress, 99)

                # 转录音频
                result = whisper_model.transcribe(
                    audio_path,
                    initial_prompt=f"以下是普通话的句子。这是一个关于{file_identifier}的视频。"
                )

                # 提取文本
                text = "".join([segment["text"] for segment in result["segments"] if segment is not None])
                log(f"转换结果: {text[:50]}...")

                # 写入文件
                f.write(text)
                f.write("\n")

        return True
    except Exception as e:
        log(f"转换文本时出错: {str(e)}", "ERROR")
        return False


def process_video_task(video_url, model="small"):
    """处理视频任务的线程函数"""
    global TASK_STATUS

    try:
        TASK_STATUS["is_processing"] = True

        # 提取BV号
        bv_number = extract_bv_number(video_url)
        if not bv_number:
            TASK_STATUS["error"] = "无效的视频链接"
            TASK_STATUS["is_processing"] = False
            return

        # 调用处理函数
        process_video(bv_number, model)

    except Exception as e:
        TASK_STATUS["error"] = f"处理过程中发生错误: {str(e)}"
        log(f"处理任务时发生错误: {str(e)}", "ERROR")
        TASK_STATUS["is_processing"] = False


# 路由定义保持不变
@bili2text_bp.route('/')
def index():
    """视频转文本页面"""
    return render_template('bili2text.html')


@bili2text_bp.route('/process', methods=['POST'])
def process():
    """开始处理视频"""
    if TASK_STATUS["is_processing"]:
        return jsonify({"success": False, "message": "已有任务正在处理中"})

    try:
        data = request.get_json()
        video_url = data.get('video_url')
        model = data.get('model', 'small')

        if not video_url:
            return jsonify({"success": False, "message": "缺少视频链接"})

        # 重置状态
        reset_task_status()

        # 生成任务ID
        task_id = str(uuid.uuid4())
        TASK_STATUS["task_id"] = task_id

        # 启动处理线程
        thread = threading.Thread(target=process_video_task, args=(video_url, model))
        thread.start()

        return jsonify({
            "success": True,
            "message": "任务已启动",
            "task_id": task_id
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"启动任务失败: {str(e)}"})


@bili2text_bp.route('/status')
def status():
    """获取当前任务状态"""
    return jsonify(TASK_STATUS)


@bili2text_bp.route('/result/<filename>')
def result(filename):
    """获取转换结果"""
    try:
        return send_from_directory('outputs', filename)
    except Exception as e:
        return f"获取结果失败: {str(e)}", 404
