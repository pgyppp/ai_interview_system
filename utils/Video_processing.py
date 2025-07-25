import cv2
import os
from moviepy import VideoFileClip
from dotenv import load_dotenv
from .xf_api import RequestApi


class InterviewProcessor:
    def __init__(self, video_path, appid, secret_key, frame_interval=8, fps_target=8):
        """初始化处理器，所有输出统一到output文件夹"""
        self.video_path = video_path
        self.appid = appid
        self.secret_key = secret_key
        self.frame_interval = frame_interval
        self.fps_target = fps_target

        # 生成递增序号（从文件记录中读取并更新）
        self.sequence = self.get_next_sequence()

        # 定义主输出文件夹
        self.main_output_dir = "output"
        # 按序号和类型细分的子路径
        self.task_dir = os.path.join(self.main_output_dir, f"task_{self.sequence}")  # 每个任务的根目录
        self.audio_output_path = os.path.join(self.task_dir, "audio.wav")  # 音频文件
        self.frames_output_dir = os.path.join(self.task_dir, "frames")      # 帧图像目录
        self.text_output_path = os.path.join(self.task_dir, "transcript.txt")  # 文本文件

        # 确保主输出目录和任务目录存在
        os.makedirs(self.task_dir, exist_ok=True)
        os.makedirs(self.frames_output_dir, exist_ok=True)

    @staticmethod
    def get_next_sequence():
        """从序号记录文件获取下一个序号"""
        seq_file = os.path.join("output", "processing_sequence.txt")  # 序号文件也放入output
        # 确保output目录存在（首次运行时）
        os.makedirs("output", exist_ok=True)
        
        if not os.path.exists(seq_file):
            with open(seq_file, "w", encoding="utf-8") as f:
                f.write("0")  # 初始序号为0
            return 0
        # 读取当前序号并递增
        with open(seq_file, "r", encoding="utf-8") as f:
            try:
                current = int(f.read().strip())
            except ValueError:
                current = 0  # 若文件内容无效，从0开始
        next_seq = current + 1
        with open(seq_file, "w", encoding="utf-8") as f:
            f.write(str(next_seq))
        return next_seq

    def extract_frames(self):
        """提取视频帧到 task_{序号}/frames 目录"""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise FileNotFoundError("无法打开视频文件")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        print(f"视频总时长: {duration:.2f} 秒")
        print(f"原始帧率: {fps:.2f} FPS")

        frame_count = 0
        second = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            current_second = int(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)

            # 每隔指定秒数保存一帧
            if current_second % self.frame_interval == 0 and current_second != second:
                frame_count += 1
                second = current_second
                frame_filename = os.path.join(self.frames_output_dir, f"frame_{second}s.jpg")
                cv2.imwrite(frame_filename, frame)
                print(f"已保存帧: {frame_filename}")

        cap.release()
        print(f"共提取 {frame_count} 帧图像（保存目录：{self.frames_output_dir}）")

    def extract_audio(self):
        """提取音频到 task_{序号}/audio.wav"""
        try:
            clip = VideoFileClip(self.video_path)
            clip.audio.write_audiofile(self.audio_output_path, codec='pcm_s16le')
            print(f"音频已保存至 {self.audio_output_path}")
        except Exception as e:
            print(f"提取音频失败: {e}")

    def audio_to_text(self) -> str | None:
        """语音转写并保存到 task_{序号}/transcript.txt"""
        try:
            api = RequestApi(
                appid=self.appid,
                secret_key=self.secret_key,
                upload_file_path=self.audio_output_path,
            )
            transcribed_text = api.get_result()

            if transcribed_text is not None:
                with open(self.text_output_path, "w", encoding="utf-8") as f:
                    f.write(transcribed_text)
                print(f"转写文本已保存到 {self.text_output_path}")
                return transcribed_text
            else:
                print("讯飞 API 未返回有效转写文本")
                return None
        except Exception as e:
            print(f"请求讯飞 API 失败: {e}")
            return None

    def run_pipeline(self):
        """运行完整处理流程"""
        print(f"开始处理视频（任务序号：{self.sequence}）...")
        print(f"所有结果将保存至：{self.task_dir}\n")

        print("[1/3] 正在提取视频帧...")
        self.extract_frames()

        print("\n[2/3] 正在提取音频...")
        self.extract_audio()

        print("\n[3/3] 正在进行语音识别...")
        text_result = self.audio_to_text()
        
        if text_result:
            print(f"\n✅ 所有任务已完成！结果汇总：")
            print(f" - 任务根目录：{self.task_dir}")
            print(f" - 音频文件：{self.audio_output_path}")
            print(f" - 帧图像目录：{self.frames_output_dir}")
            print(f" - 转写文本：{self.text_output_path}")
        else:
            print("\n⚠️ 视频处理完成，但语音转写失败或未返回结果。")


# 示例用法
# if __name__ == "__main__":
#     load_dotenv()
#     APPID = os.getenv("XF_APPID")
#     SECRET_KEY = os.getenv("XF_SECRET_KEY")
    
#     if not APPID or not SECRET_KEY:
#         print("错误：未能从.env文件中加载讯飞API凭证。请确保.env文件中包含XF_APPID和XF_SECRET_KEY。")
#         exit(1)
        
#     processor = InterviewProcessor(
#         video_path="./video/python_test.mp4",  # 可替换为任意视频路径
#         appid=APPID,
#         secret_key=SECRET_KEY,
#         frame_interval=6  # 每4秒截取一帧
#     )
#     processor.run_pipeline()