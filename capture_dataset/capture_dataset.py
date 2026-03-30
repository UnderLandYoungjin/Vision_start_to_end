# 파일 경로: ./capture_dataset_gui.py
# 이 파일은 YOLO 데이터셋용 사진을 수동으로 촬영하고, 미리 지정한 해상도와 저장 방식으로 저장하는 GUI 프로그램입니다.

import os  # 운영체제의 폴더 생성, 경로 처리 등을 위해 사용하는 표준 라이브러리입니다.
import time  # 파일명에 시간을 넣기 위해 사용하는 표준 라이브러리입니다.
import tkinter as tk  # Python 기본 GUI를 만들기 위한 tkinter 모듈입니다.
from tkinter import ttk  # tkinter의 조금 더 정돈된 위젯을 쓰기 위한 모듈입니다.
from tkinter import filedialog  # 저장 폴더를 선택하는 대화상자를 띄우기 위한 모듈입니다.
from tkinter import messagebox  # 안내창, 경고창 등을 띄우기 위한 모듈입니다.

import cv2  # 카메라 프레임을 읽고 이미지 저장/리사이즈를 처리하기 위한 OpenCV 모듈입니다.
from PIL import Image  # OpenCV 프레임을 Tkinter에 표시 가능한 이미지로 바꾸기 위해 사용하는 Pillow 모듈입니다.
from PIL import ImageTk  # Pillow 이미지를 Tkinter 화면에 올릴 수 있는 객체로 바꾸기 위한 모듈입니다.


class DatasetCaptureApp:  # 전체 GUI 프로그램을 담당하는 클래스를 정의합니다.
    def __init__(self, root):  # 클래스가 처음 만들어질 때 실행되는 초기화 함수입니다.
        self.root = root  # 전달받은 tkinter 루트 윈도우를 클래스 내부에 저장합니다.
        self.root.title("YOLO 데이터셋 수동 촬영 프로그램")  # 프로그램 창 제목을 설정합니다.
        self.root.geometry("1200x820")  # 프로그램 창의 시작 크기를 지정합니다.
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # 창을 닫을 때 on_close 함수가 실행되도록 연결합니다.

        self.camera_index = tk.IntVar(value=0)  # 사용할 카메라 번호를 저장하는 변수입니다. 기본값은 0번 카메라입니다.
        self.class_name = tk.StringVar(value="object")  # 저장할 클래스 이름 폴더명을 저장하는 변수입니다.
        self.save_dir = tk.StringVar(value=os.path.abspath("./dataset_images"))  # 기본 저장 폴더 경로를 저장하는 변수입니다.
        self.file_prefix = tk.StringVar(value="img")  # 저장 파일명 앞부분에 붙을 접두어를 저장하는 변수입니다.
        self.save_width = tk.IntVar(value=640)  # 저장할 이미지의 가로 해상도를 저장하는 변수입니다.
        self.save_height = tk.IntVar(value=640)  # 저장할 이미지의 세로 해상도를 저장하는 변수입니다.
        self.display_width = 960  # GUI 미리보기 화면에서 표시할 가로 크기를 저장합니다.
        self.display_height = 540  # GUI 미리보기 화면에서 표시할 세로 크기를 저장합니다.
        self.capture_count = tk.IntVar(value=0)  # 현재 실행 중 몇 장을 저장했는지 표시하기 위한 변수입니다.
        self.status_text = tk.StringVar(value="대기 중")  # 하단 상태 표시 문자열을 저장하는 변수입니다.
        self.resize_mode = tk.StringVar(value="letterbox")  # 저장 방식으로 letterbox 또는 stretch 중 무엇을 쓸지 저장하는 변수입니다.
        self.jpeg_quality = tk.IntVar(value=95)  # JPG 저장 품질을 조절하기 위한 변수입니다.
        self.show_grid = tk.BooleanVar(value=True)  # 미리보기 화면에 가이드 격자를 그릴지 여부를 저장하는 변수입니다.
        self.auto_mkdir_split = tk.BooleanVar(value=True)  # 클래스명 기준 하위 폴더를 자동 생성할지 여부를 저장하는 변수입니다.

        self.cap = None  # OpenCV의 VideoCapture 객체를 나중에 담기 위한 변수입니다.
        self.current_frame = None  # 현재 카메라에서 읽은 원본 프레임을 저장할 변수입니다.
        self.preview_image_tk = None  # Tkinter 라벨에 표시할 이미지 객체를 유지하기 위한 변수입니다.
        self.running = False  # 카메라 루프가 현재 동작 중인지 여부를 저장하는 변수입니다.

        self.build_ui()  # 화면의 위젯들을 생성하는 함수를 호출합니다.
        self.open_camera()  # 프로그램 시작과 동시에 기본 카메라를 여는 함수를 호출합니다.
        self.update_frame()  # 카메라 프레임을 주기적으로 갱신하는 루프를 시작합니다.

    def build_ui(self):  # GUI 위젯들을 만드는 함수입니다.
        top_frame = ttk.Frame(self.root, padding=10)  # 상단 설정 영역을 담을 프레임을 생성합니다.
        top_frame.pack(side=tk.TOP, fill=tk.X)  # 상단 프레임을 창 위쪽에 가로로 꽉 차게 배치합니다.

        preview_frame = ttk.Frame(self.root, padding=10)  # 미리보기 화면을 담을 프레임을 생성합니다.
        preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)  # 미리보기 프레임을 남는 공간까지 확장되도록 배치합니다.

        bottom_frame = ttk.Frame(self.root, padding=10)  # 하단 상태/버튼 영역을 담을 프레임을 생성합니다.
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)  # 하단 프레임을 창 아래쪽에 가로로 꽉 차게 배치합니다.

        ttk.Label(top_frame, text="카메라 번호").grid(row=0, column=0, padx=5, pady=5, sticky="w")  # 카메라 번호 라벨을 배치합니다.
        ttk.Entry(top_frame, textvariable=self.camera_index, width=8).grid(row=0, column=1, padx=5, pady=5, sticky="w")  # 카메라 번호 입력칸을 배치합니다.
        ttk.Button(top_frame, text="카메라 다시 열기", command=self.reopen_camera).grid(row=0, column=2, padx=5, pady=5)  # 카메라 다시 열기 버튼을 배치합니다.

        ttk.Label(top_frame, text="클래스 이름").grid(row=0, column=3, padx=5, pady=5, sticky="w")  # 클래스 이름 라벨을 배치합니다.
        ttk.Entry(top_frame, textvariable=self.class_name, width=20).grid(row=0, column=4, padx=5, pady=5, sticky="w")  # 클래스 이름 입력칸을 배치합니다.

        ttk.Label(top_frame, text="파일 접두어").grid(row=0, column=5, padx=5, pady=5, sticky="w")  # 파일 접두어 라벨을 배치합니다.
        ttk.Entry(top_frame, textvariable=self.file_prefix, width=15).grid(row=0, column=6, padx=5, pady=5, sticky="w")  # 파일 접두어 입력칸을 배치합니다.

        ttk.Label(top_frame, text="저장 폴더").grid(row=1, column=0, padx=5, pady=5, sticky="w")  # 저장 폴더 라벨을 배치합니다.
        ttk.Entry(top_frame, textvariable=self.save_dir, width=60).grid(row=1, column=1, columnspan=5, padx=5, pady=5, sticky="we")  # 저장 폴더 경로 입력칸을 배치합니다.
        ttk.Button(top_frame, text="폴더 선택", command=self.choose_folder).grid(row=1, column=6, padx=5, pady=5)  # 폴더 선택 버튼을 배치합니다.

        ttk.Label(top_frame, text="저장 해상도").grid(row=2, column=0, padx=5, pady=5, sticky="w")  # 저장 해상도 라벨을 배치합니다.
        ttk.Entry(top_frame, textvariable=self.save_width, width=8).grid(row=2, column=1, padx=(5, 0), pady=5, sticky="w")  # 저장 가로 해상도 입력칸을 배치합니다.
        ttk.Label(top_frame, text="x").grid(row=2, column=1, padx=(65, 0), pady=5, sticky="w")  # 해상도 구분용 x 라벨을 배치합니다.
        ttk.Entry(top_frame, textvariable=self.save_height, width=8).grid(row=2, column=1, padx=(85, 0), pady=5, sticky="w")  # 저장 세로 해상도 입력칸을 배치합니다.

        ttk.Button(top_frame, text="640x640", command=lambda: self.set_resolution(640, 640)).grid(row=2, column=2, padx=5, pady=5)  # 640x640 프리셋 버튼을 배치합니다.
        ttk.Button(top_frame, text="1280x720", command=lambda: self.set_resolution(1280, 720)).grid(row=2, column=3, padx=5, pady=5)  # 1280x720 프리셋 버튼을 배치합니다.
        ttk.Button(top_frame, text="1920x1080", command=lambda: self.set_resolution(1920, 1080)).grid(row=2, column=4, padx=5, pady=5)  # 1920x1080 프리셋 버튼을 배치합니다.

        ttk.Label(top_frame, text="저장 방식").grid(row=2, column=5, padx=5, pady=5, sticky="w")  # 저장 방식 라벨을 배치합니다.
        ttk.Combobox(top_frame, textvariable=self.resize_mode, values=["letterbox", "stretch"], width=12, state="readonly").grid(row=2, column=6, padx=5, pady=5, sticky="w")  # 저장 방식 콤보박스를 배치합니다.

        ttk.Label(top_frame, text="JPG 품질").grid(row=3, column=0, padx=5, pady=5, sticky="w")  # JPG 품질 라벨을 배치합니다.
        ttk.Scale(top_frame, from_=70, to=100, variable=self.jpeg_quality, orient=tk.HORIZONTAL, length=180).grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="w")  # JPG 품질 슬라이더를 배치합니다.

        ttk.Checkbutton(top_frame, text="가이드 격자 표시", variable=self.show_grid).grid(row=3, column=3, padx=5, pady=5, sticky="w")  # 미리보기 격자 표시 체크박스를 배치합니다.
        ttk.Checkbutton(top_frame, text="클래스별 하위 폴더 자동 생성", variable=self.auto_mkdir_split).grid(row=3, column=4, columnspan=2, padx=5, pady=5, sticky="w")  # 클래스 폴더 자동 생성 체크박스를 배치합니다.

        self.preview_label = ttk.Label(preview_frame)  # 카메라 미리보기 이미지를 표시할 라벨을 생성합니다.
        self.preview_label.pack(fill=tk.BOTH, expand=True)  # 미리보기 라벨을 프레임 안에 꽉 차게 배치합니다.

        ttk.Button(bottom_frame, text="사진 저장", command=self.save_current_frame).pack(side=tk.LEFT, padx=5, pady=5)  # 현재 프레임을 저장하는 버튼을 배치합니다.
        ttk.Button(bottom_frame, text="저장 폴더 열기", command=self.open_save_folder).pack(side=tk.LEFT, padx=5, pady=5)  # 저장 폴더를 여는 버튼을 배치합니다.

        ttk.Label(bottom_frame, text="단축키: Space=촬영 / S=촬영 / Q=종료").pack(side=tk.LEFT, padx=15)  # 단축키 안내 문구를 배치합니다.
        ttk.Label(bottom_frame, text="저장 수량:").pack(side=tk.RIGHT, padx=(5, 0))  # 저장 수량 안내 라벨을 배치합니다.
        ttk.Label(bottom_frame, textvariable=self.capture_count).pack(side=tk.RIGHT, padx=(0, 10))  # 저장된 장수 표시 라벨을 배치합니다.
        ttk.Label(bottom_frame, textvariable=self.status_text).pack(side=tk.LEFT, padx=10)  # 상태 문자열 표시 라벨을 배치합니다.

        self.root.bind("<space>", lambda event: self.save_current_frame())  # 스페이스바를 누르면 현재 프레임을 저장하도록 연결합니다.
        self.root.bind("<KeyPress-s>", lambda event: self.save_current_frame())  # 키보드 s를 누르면 현재 프레임을 저장하도록 연결합니다.
        self.root.bind("<KeyPress-S>", lambda event: self.save_current_frame())  # 대문자 S를 눌러도 저장되도록 연결합니다.
        self.root.bind("<KeyPress-q>", lambda event: self.on_close())  # 키보드 q를 누르면 프로그램이 종료되도록 연결합니다.
        self.root.bind("<KeyPress-Q>", lambda event: self.on_close())  # 대문자 Q를 눌러도 종료되도록 연결합니다.

    def set_resolution(self, width, height):  # 프리셋 해상도 버튼을 눌렀을 때 호출되는 함수입니다.
        self.save_width.set(width)  # 선택한 가로 해상도를 변수에 저장합니다.
        self.save_height.set(height)  # 선택한 세로 해상도를 변수에 저장합니다.
        self.status_text.set(f"저장 해상도 변경: {width}x{height}")  # 현재 상태창에 해상도 변경 내용을 표시합니다.

    def choose_folder(self):  # 저장 폴더를 사용자가 직접 선택하는 함수입니다.
        selected_dir = filedialog.askdirectory(initialdir=self.save_dir.get(), title="저장 폴더 선택")  # 폴더 선택 대화상자를 띄웁니다.
        if selected_dir:  # 사용자가 폴더를 정상적으로 선택했다면 아래 코드를 실행합니다.
            self.save_dir.set(selected_dir)  # 선택한 폴더 경로를 저장 변수에 반영합니다.
            self.status_text.set(f"저장 폴더 선택 완료: {selected_dir}")  # 상태창에 폴더 선택 완료 메시지를 표시합니다.

    def open_camera(self):  # 카메라를 열기 위한 함수입니다.
        self.release_camera()  # 혹시 기존 카메라가 열려 있으면 먼저 안전하게 닫습니다.
        self.cap = cv2.VideoCapture(self.camera_index.get(), cv2.CAP_DSHOW)  # 지정한 카메라 번호로 VideoCapture 객체를 생성합니다.
        if not self.cap.isOpened():  # 카메라가 정상적으로 열리지 않았다면 아래 코드를 실행합니다.
            self.status_text.set("카메라 열기 실패")  # 상태창에 카메라 실패 메시지를 표시합니다.
            messagebox.showerror("오류", "카메라를 열 수 없습니다. 카메라 번호를 확인하세요.")  # 오류 메시지 박스를 띄웁니다.
            self.running = False  # 카메라 루프를 중지 상태로 표시합니다.
            return  # 더 이상 진행하지 않고 함수를 종료합니다.
        self.running = True  # 카메라가 정상적으로 열렸으므로 루프 동작 상태를 True로 설정합니다.
        self.status_text.set(f"카메라 열림: index={self.camera_index.get()}")  # 상태창에 열린 카메라 번호를 표시합니다.
        
    def reopen_camera(self):  # 사용자가 카메라 다시 열기 버튼을 눌렀을 때 실행되는 함수입니다.
        self.open_camera()  # 카메라를 다시 여는 기존 함수를 호출합니다.

    def release_camera(self):  # 현재 열려 있는 카메라 자원을 해제하는 함수입니다.
        if self.cap is not None:  # 카메라 객체가 존재하는 경우에만 아래 코드를 실행합니다.
            self.cap.release()  # OpenCV 카메라 자원을 운영체제에 반환합니다.
            self.cap = None  # 카메라 객체 참조를 비워 둡니다.

    def letterbox_image(self, frame, target_width, target_height):  # 원본 비율을 유지하면서 목표 크기 캔버스에 맞추는 함수입니다.
        src_height, src_width = frame.shape[:2]  # 원본 프레임의 세로, 가로 크기를 가져옵니다.
        scale = min(target_width / src_width, target_height / src_height)  # 가로/세로 중 더 먼저 맞는 축 기준으로 축소 또는 확대 비율을 계산합니다.
        new_width = int(src_width * scale)  # 비율을 유지한 새 가로 크기를 계산합니다.
        new_height = int(src_height * scale)  # 비율을 유지한 새 세로 크기를 계산합니다.
        resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)  # 비율 유지된 크기로 이미지를 리사이즈합니다.
        canvas = cv2.cvtColor(cv2.cvtColor(cv2.UMat(target_height, target_width, cv2.CV_8UC3).get(), cv2.COLOR_BGR2RGB), cv2.COLOR_RGB2BGR)  # 목표 크기의 빈 컬러 캔버스를 생성합니다.
        canvas[:] = (0, 0, 0)  # 남는 여백 부분을 검은색으로 채웁니다.
        x_offset = (target_width - new_width) // 2  # 가로 방향 중앙 정렬을 위한 시작 위치를 계산합니다.
        y_offset = (target_height - new_height) // 2  # 세로 방향 중앙 정렬을 위한 시작 위치를 계산합니다.
        canvas[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized  # 리사이즈된 이미지를 중앙에 복사합니다.
        return canvas  # 완성된 letterbox 이미지를 반환합니다.

    def stretch_image(self, frame, target_width, target_height):  # 원본 비율을 무시하고 목표 크기로 강제 변환하는 함수입니다.
        stretched = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LINEAR)  # 지정 크기로 강제 리사이즈합니다.
        return stretched  # 리사이즈된 이미지를 반환합니다.

    def prepare_save_image(self, frame):  # 저장 직전에 현재 설정에 맞는 최종 이미지를 만드는 함수입니다.
        target_width = int(self.save_width.get())  # 현재 설정된 저장 가로 크기를 가져옵니다.
        target_height = int(self.save_height.get())  # 현재 설정된 저장 세로 크기를 가져옵니다.

        if target_width <= 0 or target_height <= 0:  # 사용자가 잘못된 해상도를 넣은 경우를 검사합니다.
            raise ValueError("저장 해상도는 1 이상의 정수여야 합니다.")  # 잘못된 해상도일 경우 예외를 발생시킵니다.

        if self.resize_mode.get() == "letterbox":  # 저장 방식이 letterbox인 경우 아래 코드를 실행합니다.
            return self.letterbox_image(frame, target_width, target_height)  # letterbox 방식으로 변환한 이미지를 반환합니다.
        return self.stretch_image(frame, target_width, target_height)  # 그 외에는 stretch 방식으로 변환한 이미지를 반환합니다.

    def get_output_folder(self):  # 실제 저장될 최종 폴더 경로를 계산하는 함수입니다.
        base_dir = self.save_dir.get().strip()  # 기본 저장 폴더 문자열의 앞뒤 공백을 제거합니다.
        class_name = self.class_name.get().strip()  # 클래스 이름 문자열의 앞뒤 공백을 제거합니다.

        if not base_dir:  # 기본 저장 폴더가 비어 있으면 아래 코드를 실행합니다.
            raise ValueError("저장 폴더가 비어 있습니다.")  # 저장 폴더가 비어 있다는 예외를 발생시킵니다.

        if self.auto_mkdir_split.get():  # 클래스별 하위 폴더 생성 옵션이 켜져 있으면 아래 코드를 실행합니다.
            if not class_name:  # 클래스 이름이 비어 있으면 아래 코드를 실행합니다.
                raise ValueError("클래스 이름이 비어 있습니다.")  # 클래스 이름 누락 예외를 발생시킵니다.
            output_dir = os.path.join(base_dir, class_name)  # 기본 폴더 아래에 클래스명 폴더를 붙여 최종 경로를 만듭니다.
        else:  # 클래스별 하위 폴더를 쓰지 않는 경우 아래 코드를 실행합니다.
            output_dir = base_dir  # 기본 폴더 자체를 최종 저장 경로로 사용합니다.

        os.makedirs(output_dir, exist_ok=True)  # 최종 저장 폴더가 없으면 자동으로 생성합니다.
        return output_dir  # 계산된 최종 저장 폴더 경로를 반환합니다.

    def make_filename(self):  # 저장 파일명을 만드는 함수입니다.
        prefix = self.file_prefix.get().strip() or "img"  # 접두어가 비어 있으면 기본값 img를 사용합니다.
        class_name = self.class_name.get().strip() or "object"  # 클래스명이 비어 있으면 기본값 object를 사용합니다.
        timestamp = time.strftime("%Y%m%d_%H%M%S")  # 현재 시간을 파일명에 넣기 좋은 형태의 문자열로 변환합니다.
        millis = int((time.time() % 1) * 1000)  # 같은 초 안에서 여러 장 저장될 때 파일명 중복을 줄이기 위해 밀리초 값을 계산합니다.
        filename = f"{prefix}_{class_name}_{timestamp}_{millis:03d}.jpg"  # 최종 JPG 파일명을 조합합니다.
        return filename  # 만들어진 파일명을 반환합니다.

    def save_current_frame(self):  # 현재 프레임을 디스크에 저장하는 핵심 함수입니다.
        if self.current_frame is None:  # 아직 프레임이 준비되지 않았다면 아래 코드를 실행합니다.
            self.status_text.set("저장 실패: 현재 프레임 없음")  # 상태창에 저장 실패 사유를 표시합니다.
            return  # 더 이상 진행하지 않고 함수를 종료합니다.

        try:  # 저장 과정에서 오류가 날 수 있으므로 예외 처리를 시작합니다.
            output_dir = self.get_output_folder()  # 실제 저장할 폴더 경로를 계산합니다.
            save_image = self.prepare_save_image(self.current_frame)  # 현재 프레임을 지정 방식과 해상도로 변환합니다.
            filename = self.make_filename()  # 저장 파일명을 생성합니다.
            full_path = os.path.join(output_dir, filename)  # 저장 폴더와 파일명을 합쳐 최종 경로를 만듭니다.
            quality = int(self.jpeg_quality.get())  # 현재 JPG 품질 값을 정수로 가져옵니다.
            success = cv2.imwrite(full_path, save_image, [cv2.IMWRITE_JPEG_QUALITY, quality])  # OpenCV로 JPG 파일을 실제 저장합니다.

            if not success:  # OpenCV 저장 결과가 실패라면 아래 코드를 실행합니다.
                raise RuntimeError("cv2.imwrite 저장 실패")  # 저장 실패 예외를 발생시킵니다.

            self.capture_count.set(self.capture_count.get() + 1)  # 저장 성공 시 저장 장수 카운트를 1 증가시킵니다.
            self.status_text.set(f"저장 완료: {full_path}")  # 상태창에 저장 완료 경로를 표시합니다.
        except Exception as e:  # 저장 중 발생한 모든 예외를 받아서 처리합니다.
            self.status_text.set(f"저장 실패: {e}")  # 상태창에 실패 원인을 문자열로 표시합니다.
            messagebox.showerror("저장 오류", str(e))  # 사용자에게 오류 메시지 창을 띄웁니다.

    def draw_preview_guides(self, frame):  # 미리보기 화면에 가이드 선을 그리는 함수입니다.
        preview = frame.copy()  # 원본 프레임을 손상시키지 않기 위해 복사본을 만듭니다.
        h, w = preview.shape[:2]  # 미리보기 프레임의 높이와 너비를 가져옵니다.

        if self.show_grid.get():  # 가이드 격자 표시 옵션이 켜져 있으면 아래 코드를 실행합니다.
            cv2.line(preview, (w // 2, 0), (w // 2, h), (0, 255, 0), 1)  # 세로 중앙선을 녹색으로 그립니다.
            cv2.line(preview, (0, h // 2), (w, h // 2), (0, 255, 0), 1)  # 가로 중앙선을 녹색으로 그립니다.
            cv2.rectangle(preview, (w // 4, h // 4), (w * 3 // 4, h * 3 // 4), (255, 0, 0), 1)  # 중앙 기준 박스를 파란색으로 그립니다.

        info_text_1 = f"Save: {self.save_width.get()}x{self.save_height.get()} / Mode: {self.resize_mode.get()}"  # 현재 저장 해상도와 저장 방식을 안내 문자열로 만듭니다.
        info_text_2 = f"Class: {self.class_name.get()} / Count: {self.capture_count.get()}"  # 현재 클래스명과 저장 수량을 안내 문자열로 만듭니다.
        cv2.putText(preview, info_text_1, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)  # 첫 번째 안내 문구를 화면 상단에 그립니다.
        cv2.putText(preview, info_text_2, (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)  # 두 번째 안내 문구를 화면 상단에 그립니다.

        return preview  # 가이드와 문구가 그려진 미리보기 프레임을 반환합니다.

    def update_frame(self):  # 카메라 프레임을 지속적으로 읽어서 GUI에 표시하는 함수입니다.
        if self.running and self.cap is not None:  # 카메라가 정상 동작 중이라면 아래 코드를 실행합니다.
            ret, frame = self.cap.read()  # 카메라에서 프레임 1장을 읽어옵니다.
            if ret and frame is not None:  # 프레임 읽기가 성공했다면 아래 코드를 실행합니다.
                self.current_frame = frame.copy()  # 현재 프레임 원본을 저장용으로 별도 보관합니다.
                preview = self.draw_preview_guides(frame)  # 화면 표시용 가이드가 들어간 프레임을 생성합니다.
                preview = cv2.resize(preview, (self.display_width, self.display_height), interpolation=cv2.INTER_LINEAR)  # GUI 표시용 고정 크기로 리사이즈합니다.
                preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)  # OpenCV의 BGR 색상 순서를 Tkinter용 RGB 순서로 변환합니다.
                pil_image = Image.fromarray(preview_rgb)  # numpy 배열 이미지를 Pillow 이미지 객체로 변환합니다.
                self.preview_image_tk = ImageTk.PhotoImage(image=pil_image)  # Pillow 이미지를 Tkinter 라벨에 넣을 수 있는 객체로 변환합니다.
                self.preview_label.configure(image=self.preview_image_tk)  # 변환된 이미지를 GUI 라벨에 표시합니다.
            else:  # 프레임 읽기에 실패했다면 아래 코드를 실행합니다.
                self.status_text.set("프레임 읽기 실패")  # 상태창에 프레임 읽기 실패 메시지를 표시합니다.

        self.root.after(15, self.update_frame)  # 약 15ms 후에 update_frame을 다시 호출하여 실시간 화면을 유지합니다.

    def open_save_folder(self):  # 저장 폴더를 탐색기에서 여는 함수입니다.
        try:  # 폴더 열기 중 오류 가능성이 있으므로 예외 처리를 시작합니다.
            output_dir = self.get_output_folder()  # 현재 설정 기준 실제 저장 폴더 경로를 계산합니다.
            os.startfile(output_dir)  # Windows 탐색기로 해당 폴더를 엽니다.
        except Exception as e:  # 폴더 열기 중 발생한 예외를 처리합니다.
            messagebox.showerror("폴더 열기 오류", str(e))  # 오류 내용을 메시지 박스로 표시합니다.

    def on_close(self):  # 프로그램 종료 시 정리 작업을 하는 함수입니다.
        self.running = False  # 프레임 업데이트 루프의 동작 상태를 중지로 바꿉니다.
        self.release_camera()  # 카메라 자원을 안전하게 해제합니다.
        self.root.destroy()  # tkinter 메인 창을 종료합니다.


def main():  # 프로그램 시작 진입점 역할을 하는 함수입니다.
    root = tk.Tk()  # tkinter 메인 윈도우를 생성합니다.
    app = DatasetCaptureApp(root)  # GUI 애플리케이션 클래스를 생성하여 윈도우와 연결합니다.
    root.mainloop()  # tkinter 이벤트 루프를 시작하여 프로그램이 계속 실행되도록 합니다.


if __name__ == "__main__":  # 이 파일이 직접 실행되었을 때만 아래 코드를 실행하기 위한 조건문입니다.
    main()  # 프로그램 시작 함수를 호출합니다.
