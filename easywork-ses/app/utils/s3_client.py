import aioboto3
import os
from typing import Optional, BinaryIO
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class S3Client:
    """AWS S3通用クライアント（非同期対応）"""
    
    def __init__(self):
        self.bucket_name = "tob-easywork"
        self.region = "ap-northeast-1"
        self.endpoint_url = "https://s3.ap-northeast-1.amazonaws.com"
        
        # 認証情報
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        self.session = aioboto3.Session()
    
    async def upload_file(self, file_path: str, s3_key: str, content_type: Optional[str] = None) -> str:
        """
        ローカルファイルをS3にアップロード
        
        Args:
            file_path: アップロードするファイルのパス
            s3_key: S3オブジェクトキー
            content_type: ファイルのMIMEタイプ
            
        Returns:
            S3オブジェクトのURL
        """
        try:
            async with self.session.client(
                's3',
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            ) as s3:
                extra_args = {}
                if content_type:
                    extra_args['ContentType'] = content_type
                
                # ファイルをアップロード
                await s3.upload_file(
                    file_path,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs=extra_args
                )
                
                # URLを生成
                url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
                logger.info(f"ファイルアップロード成功: {url}")
                return url
                
        except FileNotFoundError:
            logger.error(f"ファイルが見つかりません: {file_path}")
            raise
        except ClientError as e:
            logger.error(f"S3アップロードエラー: {str(e)}")
            raise
    
    async def upload_fileobj(self, fileobj: BinaryIO, s3_key: str, content_type: Optional[str] = None) -> str:
        """
        ファイルオブジェクトをS3にアップロード
        
        Args:
            fileobj: アップロードするファイルオブジェクト
            s3_key: S3オブジェクトキー
            content_type: ファイルのMIMEタイプ
            
        Returns:
            S3オブジェクトのURL
        """
        try:
            async with self.session.client(
                's3',
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            ) as s3:
                extra_args = {}
                if content_type:
                    extra_args['ContentType'] = content_type
                
                # ファイルオブジェクトをアップロード
                await s3.upload_fileobj(
                    fileobj,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs=extra_args
                )
                
                # URLを生成
                url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
                logger.info(f"ファイルオブジェクトアップロード成功: {url}")
                return url
                
        except ClientError as e:
            logger.error(f"S3アップロードエラー: {str(e)}")
            raise
    
    async def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        S3からファイルをダウンロード
        
        Args:
            s3_key: S3オブジェクトキー
            local_path: ダウンロード先ローカルパス
            
        Returns:
            成功時True
        """
        try:
            async with self.session.client(
                's3',
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            ) as s3:
                await s3.download_file(self.bucket_name, s3_key, local_path)
                logger.info(f"ファイルダウンロード成功: {local_path}")
                return True
                
        except ClientError as e:
            logger.error(f"S3ダウンロードエラー: {str(e)}")
            return False
    
    async def delete_file(self, s3_key: str) -> bool:
        """
        S3からファイルを削除
        
        Args:
            s3_key: 削除するS3オブジェクトキー
            
        Returns:
            成功時True
        """
        try:
            async with self.session.client(
                's3',
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            ) as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
                logger.info(f"ファイル削除成功: {s3_key}")
                return True
                
        except ClientError as e:
            logger.error(f"S3削除エラー: {str(e)}")
            return False
    
    async def file_exists(self, s3_key: str) -> bool:
        """
        S3にファイルが存在するかチェック
        
        Args:
            s3_key: チェックするS3オブジェクトキー
            
        Returns:
            存在する場合True
        """
        try:
            async with self.session.client(
                's3',
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            ) as s3:
                await s3.head_object(Bucket=self.bucket_name, Key=s3_key)
                return True
                
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"S3存在チェックエラー: {str(e)}")
                raise
    
    async def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        署名付きURLを生成

        Args:
            s3_key: S3オブジェクトキー
            expiration: URL有効期限（秒）

        Returns:
            署名付きURL
        """
        try:
            async with self.session.client(
                's3',
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            ) as s3:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration
                )
                return url

        except ClientError as e:
            logger.error(f"署名付きURL生成エラー: {str(e)}")
            raise

    async def get_file_content(self, s3_key: str) -> Optional[bytes]:
        """
        S3からファイル内容を取得（メモリ上で）

        Args:
            s3_key: S3オブジェクトキー

        Returns:
            ファイル内容のバイト列、取得失敗時はNone
        """
        try:
            async with self.session.client(
                's3',
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            ) as s3:
                response = await s3.get_object(Bucket=self.bucket_name, Key=s3_key)
                file_content = await response['Body'].read()
                logger.info(f"ファイル内容取得成功: {s3_key}, サイズ: {len(file_content)} bytes")
                return file_content

        except ClientError as e:
            logger.error(f"S3ファイル内容取得エラー: {str(e)}")
            return None


# グローバルインスタンス
s3_client = S3Client()