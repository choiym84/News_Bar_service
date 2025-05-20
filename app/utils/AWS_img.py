import boto3
import os
from dotenv import load_dotenv
import requests
from io import BytesIO
load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
    
def upload_image_to_s3_from_url(img_url: str, s3_key: str) -> str:

    bucket_name = os.getenv("S3_BUCKET_NAME")
    try:
        response = requests.get(img_url)
        response.raise_for_status()
        
        # 파일 업로드 (파일 객체, 버킷, 키)
        
        filename = s3_key.split("/")[-1]
        s3_key_final = f"article_img/{filename}.jpg"

        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key_final,
            Body=response.content,
            ContentType='image/jpeg'  # 또는 'image/png' 등
        )
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/article_img/{s3_key_final}"
        return s3_url

    except Exception as e:
        
        url = f"https://{bucket_name}.s3.amazonaws.com/article_img/NoExistThumbnail.jpg"
        print(f"이미지 업로드 실패: {e} 기본이미지로 설정 {url}")
        return url


def download_image_to_local(img_url: str, save_dir: str = "images", file_name: str = "test_image.jpg"):
    try:
        response = requests.get(img_url)
        response.raise_for_status()  # 상태 코드가 200이 아니면 예외 발생

        # 디렉터리 없으면 생성
        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, file_name)

        with open(file_path, 'wb') as f:
            f.write(response.content)

        print(f"✅ 이미지 저장 완료: {file_path}")
        return file_path
    except Exception as e:
        print(f"❌ 이미지 다운로드 실패: {e}")
        return None
