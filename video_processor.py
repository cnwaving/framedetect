import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np  # 新增导入NumPy

# 帧差法视频处理程序 v1.0
# 功能：
# 1. 支持视频文件选择(mp4/avi/mov格式)
# 2. 实现三帧差法运动检测算法
# 3. 提供实时视频播放控制(播放/暂停)
# 4. 可调节高斯模糊参数(3-31奇数范围)
# 5. 动态阈值计算与显示(10-50范围)
# 6. 双窗口显示(原始视频+处理结果)
# 7. 自动资源释放
# 8. 错误处理机制
# 技术栈：OpenCV + Tkinter + Pillow
class VideoProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("帧差法视频处理")
        # 设置窗口大小1200x800
        self.root.geometry("1200x800")
        
        # 创建界面组件
        self.setup_ui()
        
        # 初始化视频相关变量
        self.video_path = None
        self.cap = None
        self.prev_frame = None
        self.prev_prev_frame = None  # 新增：存储前两帧
        self.is_playing = False

    def setup_ui(self):
        # 主容器框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 视频显示区域 (固定在主容器顶部)
        self.video_frame = tk.Frame(self.main_frame)
        self.video_frame.pack(side=tk.TOP, pady=10)
        
        # 原始视频窗口 (移除width/height设置)
        self.original_label = tk.Label(self.video_frame)
        self.original_label.grid(row=0, column=0, padx=10)
        
        # 处理后的视频窗口 (移除width/height设置)
        self.processed_label = tk.Label(self.video_frame)
        self.processed_label.grid(row=0, column=1, padx=10)
        
        # 控制区域 (放在主容器底部)
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.BOTTOM, pady=20)
        
        # 视频选择按钮 (放在控制区域)
        self.select_btn = tk.Button(self.control_frame, text="选择视频", command=self.select_video)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # 播放控制按钮
        self.play_btn = tk.Button(self.control_frame, text="播放", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        # 添加模糊大小调节滑块
        self.blur_label = tk.Label(self.control_frame, text="模糊大小:")
        self.blur_label.pack(side=tk.LEFT, padx=5)
        self.blur_scale = tk.Scale(self.control_frame, from_=3, to=31, resolution=2, 
                                 orient=tk.HORIZONTAL, command=self.update_blur_size)
        self.blur_scale.set(13)  # 默认值
        self.blur_scale.pack(side=tk.LEFT, padx=5)

        # 添加阈值显示标签
        self.thresh_label = tk.Label(self.control_frame, text="动态阈值: 15")
        self.thresh_label.pack(side=tk.LEFT, padx=5)

        # 确保窗口内容可见
        self.root.update()
        self.root.minsize(1200, 800)
        
    def select_video(self):
        try:
            self.video_path = filedialog.askopenfilename(filetypes=[("视频文件", "*.mp4 *.avi *.mov")])
            if self.video_path:
                self.cap = cv2.VideoCapture(self.video_path)
                if not self.cap.isOpened():
                    raise ValueError("无法打开视频文件")
                self.show_first_frame()
        except Exception as e:
            tk.messagebox.showerror("错误", f"加载视频失败: {str(e)}")
            
    def show_first_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # 调整原始帧大小以适应Label
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img = img.resize((600, 480), Image.LANCZOS)  # 强制缩放为600x480
            imgtk = ImageTk.PhotoImage(image=img)
            self.original_label.imgtk = imgtk
            self.original_label.configure(image=imgtk)
            
            # 显示处理后的帧
            processed_img = Image.fromarray(frame)
            processed_img = processed_img.resize((600, 480), Image.LANCZOS)
            processed_img = ImageTk.PhotoImage(image=processed_img)
            self.processed_label.imgtk = processed_img
            self.processed_label.configure(image=processed_img)
            
            # 重置播放状态
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.prev_frame = None

    def play_video(self):
        if not self.is_playing or not self.cap:
            return
            
        ret, frame = self.cap.read()
        if ret:
            # 显示原始帧
            original_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(original_frame)
            img = img.resize((600, 480), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.original_label.imgtk = imgtk
            self.original_label.configure(image=imgtk)
            
            # 处理帧(帧差法)
            processed_frame = self.process_frame(frame)
            processed_img = Image.fromarray(processed_frame)
            processed_img = processed_img.resize((600, 480), Image.LANCZOS)
            processed_img = ImageTk.PhotoImage(image=processed_img)
            self.processed_label.imgtk = processed_img
            self.processed_label.configure(image=processed_img)
            
            # 继续播放
            self.root.after(30, self.play_video)
        else:
            # 视频结束
            self.is_playing = False
            self.play_btn.config(text="播放")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.play_btn.config(text="暂停" if self.is_playing else "播放")
        self.play_video()
        
    def update_blur_size(self, val):
        # 滑块值改变时更新模糊大小
        self.blur_size = int(float(val))
        # 确保是奇数
        self.blur_size = self.blur_size if self.blur_size % 2 == 1 else self.blur_size + 1

    def process_frame(self, frame):
        """处理视频帧，使用三帧差法检测运动
        
        Args:
            frame: 输入的BGR格式视频帧
            
        Returns:
            处理后的三通道BGR图像，运动区域显示为白色
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur_size = getattr(self, 'blur_size', 13)  # 默认13
        gray = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
        
        if self.prev_prev_frame is None:
            self.prev_prev_frame = gray
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        elif self.prev_frame is None:
            self.prev_frame = gray
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            
        # 计算三帧差法
        diff1 = cv2.absdiff(self.prev_prev_frame, self.prev_frame)
        diff2 = cv2.absdiff(self.prev_frame, gray)
        frame_diff = cv2.bitwise_or(diff1, diff2)
        
        # 动态计算阈值
        mean_val = np.mean(frame_diff)
        dynamic_thresh = max(10, min(mean_val * 1.5, 50))  # 限制在10-50之间
        _, thresh = cv2.threshold(frame_diff, dynamic_thresh, 255, cv2.THRESH_BINARY)
        
        # 更新阈值显示
        if hasattr(self, 'thresh_label'):
            self.thresh_label.config(text=f"动态阈值: {int(dynamic_thresh)}")
        
        # 优化形态学处理
        kernel = np.ones((3,3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # 创建纯黑背景
        result = np.zeros_like(gray)
        
        # 将运动区域设为白色
        result[thresh == 255] = 255
        
        # 转换为3通道图像以便显示
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            
        # 更新帧缓存
        self.prev_prev_frame = self.prev_frame
        self.prev_frame = gray
        return result

    def __del__(self):
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoProcessor(root)
    root.mainloop()