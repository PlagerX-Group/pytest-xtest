import boto3


class AWSClient:
    def __init__(self, bucket: str, access_key: str, secret_token: str, /) -> None:
        self.bucket_name = bucket
        self.session = boto3.session.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_token,
        )
        self.s3_client = self.session.client(
            service_name="s3",
            endpoint_url="https://storage.yandexcloud.net",
        )
        self.s3_resource = self.session.resource(
            service_name="s3",
            endpoint_url="https://storage.yandexcloud.net",
        )

    def get_object_url(self, object_name: str, expires_in: int = 864000) -> str:
        return self.s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket_name, "Key": object_name},
            ExpiresIn=expires_in,
        )

    def upload_b64_object(self, resource_path: str, body_file: bytes, content_type: str = "image/png") -> None:
        s3_object = self.s3_resource.Object(self.bucket_name, resource_path)
        s3_object.put(ContentType=content_type, Body=body_file)

    def upload_txt_object(self, resource_path: str, text: str) -> None:
        s3_object = self.s3_resource.Object(self.bucket_name, resource_path)
        s3_object.put(ContentType="plain/text", Body=text)
