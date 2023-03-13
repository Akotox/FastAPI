from typing import List
import boto3
from loguru import logger
from uuid import uuid4
import magic
from fastapi import FastAPI, HTTPException, UploadFile, status
from pydantic import BaseModel


KB = 1024
MB = 1024 * KB

SUPPORTED_FILE_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'application/pdf': 'pdf'
}

AWS_BUCKET = 'my-go-micro-bucket'

s3 = boto3.resource('s3')
bucket = s3.Bucket(AWS_BUCKET)


async def s3_upload(contents: bytes, key: str):
    logger.info(f'Uploading {key} to s3')
    bucket.put_object(Key=f'images/{key}', Body=contents)


app = FastAPI()
# handler = Mangum(app)


@app.get("/")
async def home():
    return {'message': 'Hello file upload'}


@app.post('/upload')
async def upload(files: List[UploadFile] = None):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No files found'
        )

    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Max 5 files can be uploaded at once'
        )

    file_names = []
    for file in files:
        contents = await file.read()
        size = len(contents)

        if not 0 < size <= 1 * MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supported file size is 0-1 MB"
            )

        file_type = magic.from_buffer(buffer=contents, mime=True)
        if file_type not in SUPPORTED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Unsupported file type: {file_type}.'
            )
        file_name = f'{uuid4()}.{SUPPORTED_FILE_TYPES[file_type]}'
        await s3_upload(contents=contents, key=file_name)

        file_names.append(file_name)

    return {'file_names': file_names}
