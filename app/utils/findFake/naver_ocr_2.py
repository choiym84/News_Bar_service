import time
import json
import os
import uuid
import requests
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

api_url = os.getenv("api_url")  # 예: "https://ocr.api.naver.com/..."
secret_key = os.getenv("secret_key")

# 추출할 언론사 이름 목록 정의
MEDIA_NAMES = [
    "연합뉴스", "KBS", "MBC", "SBS", "YTN",
    "한겨레", "경향신문", "중앙일보", "동아일보",
    "한국일보", "서울경제", "헤럴드경제", "세계일보",
    "뉴시스", "한국경제", "조선일보", "TV조선", "채널A",
    "국민일보", "문화일보", "뉴데일리", "데일리안",
    "펜앤드마이크", "뉴스타운", "자유일보", "미디어워치",
    "오마이뉴스", "프레시안", "뉴스1", "뉴스핌",
    "이데일리", "아시아경제", "비즈니스워치"
]

def merge_boxes_by_lines(ocr_results, y_threshold=20):
    """
    OCR 결과에서 y축을 기준으로 같은 라인에 속하는 박스들을 그룹화하여
    각 라인의 텍스트를 순서대로 연결한 리스트를 반환합니다.
    """
    lines = []
    for image in ocr_results.get("images", []):
        boxes = []
        for field in image.get("fields", []):
            verts = field["boundingPoly"]["vertices"]
            ys = [v.get("y", 0) for v in verts]
            center_y = sum(ys) / len(ys)
            boxes.append({
                "text": field["inferText"],
                "min_x": min(v.get("x", 0) for v in verts),
                "center_y": center_y
            })
        if not boxes:
            continue
        boxes.sort(key=lambda b: b["center_y"])
        current_line = [boxes[0]]
        for bx in boxes[1:]:
            prev_center = sum(b['center_y'] for b in current_line) / len(current_line)
            if abs(bx['center_y'] - prev_center) <= y_threshold:
                current_line.append(bx)
            else:
                current_line.sort(key=lambda b: b['min_x'])
                lines.append(" ".join(b['text'] for b in current_line))
                current_line = [bx]
        current_line.sort(key=lambda b: b['min_x'])
        lines.append(" ".join(b['text'] for b in current_line))
    return lines


def extract_media_outlets(lines):
    """
    OCR로 추출된 각 라인에서 미리 정의된 언론사 이름이 포함된 라인을 찾아
    고유한 언론사 목록을 반환합니다.
    """
    found = set()
    for line in lines:
        for name in MEDIA_NAMES:
            if name in line:
                found.add(name)
    return list(found)


def ocr_and_extract_text(image_path):
    # OCR 요청 생성
    request_json = {
        'images': [{'format': os.path.splitext(image_path)[1].lstrip('.').lower(), 'name': 'demo'}],
        'requestId': str(uuid.uuid4()),
        'version': 'V2',
        'timestamp': int(round(time.time() * 1000))
    }
    headers = {'X-OCR-SECRET': secret_key}
    files = [('file', open(image_path, 'rb'))]
    payload = {'message': json.dumps(request_json).encode('UTF-8')}

    # API 호출
    resp = requests.post(api_url, headers=headers, data=payload, files=files)
    resp.raise_for_status()

    # 결과 파싱 및 라인 병합
    ocr_results = resp.json()
    lines = merge_boxes_by_lines(ocr_results, y_threshold=20)

    # 언론사 이름 추출
    outlets = extract_media_outlets(lines)

    # 전체 텍스트와 언론사 목록 반환
    return lines, outlets


if __name__ == '__main__':
    img_path = "/Users/hansangjun/Desktop/Capstone_Backend/news_naver_API/screenshots/first_screen.png"
    full_text, media_outlets = ocr_and_extract_text(img_path)
    print("--- 전체 텍스트 ---")
    print(full_text)
    print("\n--- 추출된 언론사 ---")
    print(media_outlets)
