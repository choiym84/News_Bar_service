import boto3
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_S3_REGION")
)

BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")


async def download_and_upload_image(session: aiohttp.ClientSession, image_url: str) -> Optional[str]:
    try:
        async with session.get(image_url) as response:
            if response.status == 200:
                img_data = await response.read()
                ext = image_url.split('.')[-1].split("?")[0]
                filename = f"news_images/{uuid.uuid4()}.{ext}"
                
                s3.upload_fileobj(
                    Fileobj=io.BytesIO(img_data),
                    Bucket=BUCKET_NAME,
                    Key=filename,
                    ExtraArgs={'ContentType': f'image/{ext}', 'ACL': 'public-read'}
                )
                return f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
            else:
                logging.warning(f"Image download failed: {image_url}")
    except Exception as e:
        logging.error(f"Error downloading image: {e}")
    return None
