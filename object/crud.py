from urllib.request import urlopen
import io
from hashlib import md5
from time import localtime
import mimetypes
from boto3.s3.transfer import TransferConfig


# ── original functions (preserved exactly) ──────────────────────────────────

def get_objects(aws_s3_client, bucket_name):
    for key in aws_s3_client.list_objects(Bucket=bucket_name)["Contents"]:
        print(f" {key['Key']}, size: {key['Size']}")


def download_file_and_upload_to_s3(
    aws_s3_client, bucket_name, url, keep_local=False
) -> str:
    file_name = f'image_file_{md5(str(localtime()).encode("utf-8")).hexdigest()}.jpg'
    with urlopen(url) as response:
        content = response.read()
        aws_s3_client.upload_fileobj(
            Fileobj=io.BytesIO(content),
            Bucket=bucket_name,
            ExtraArgs={"ContentType": "image/jpg"},
            Key=file_name,
        )
    if keep_local:
        with open(file_name, mode="wb") as jpg_file:
            jpg_file.write(content)

    # public URL
    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        "us-west-2", bucket_name, file_name
    )


def upload_file_obj(aws_s3_client, filename, bucket_name):
    with open(filename, "rb") as file:
        aws_s3_client.upload_fileobj(file, bucket_name, "hello_obj.txt")


def upload_file_put(aws_s3_client, filename, bucket_name):
    with open(filename, "rb") as file:
        aws_s3_client.put_object(
            Bucket=bucket_name, Key="hello_put.txt", Body=file.read()
        )


# ── NEW: optional MIME type validation ──────────────────────────────────────

ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/zip",
    "application/json",
]


def validate_mime_type(filename):
    """
    Checks the file's MIME type against an allow-list.
    Returns the MIME type string on success.
    Raises ValueError if the type is unknown or not allowed.
    """
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        raise ValueError(
            f"Cannot determine MIME type for '{filename}'. "
            "Ensure the file has a recognised extension."
        )
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"MIME type '{mime_type}' is not allowed.\n"
            f"Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    print(f"  [mime] {mime_type} — OK")
    return mime_type


# ── NEW: upload small file (single-part) ────────────────────────────────────

def upload_file(aws_s3_client, filename, bucket_name,
                object_name=None, validate_mime=False):
    """
    Upload a small file to S3 using a standard single-part upload.
    Recommended for files under 25 MB.

    Original upload_file() used upload_file() but had two bugs:
      1. It passed args.upload_file ("True") as the filename.
      2. upload_file() returns None, so reading response["ResponseMetadata"]
         raised a TypeError. Both are fixed here.

    Parameters
    ----------
    filename      : local path of the file to upload
    bucket_name   : destination S3 bucket
    object_name   : S3 key; defaults to the file's base name
    validate_mime : if True, validate MIME type before uploading
    """
    if object_name is None:
        object_name = filename.split("/")[-1]

    extra_args = {}
    if validate_mime:
        mime_type = validate_mime_type(filename)
        extra_args["ContentType"] = mime_type

    aws_s3_client.upload_file(
        filename, bucket_name, object_name,
        ExtraArgs=extra_args if extra_args else None,
    )
    print(f"  Uploaded (small/single-part): '{filename}' → s3://{bucket_name}/{object_name}")
    return True


# ── NEW: upload large file (multipart) ──────────────────────────────────────

def upload_large_file(aws_s3_client, filename, bucket_name,
                      object_name=None, validate_mime=False):
    """
    Upload a large file to S3 using multipart upload with parallel threads.
    boto3 splits the file into 25 MB chunks, uploads them concurrently
    (up to 10 threads), then S3 assembles them server-side.
    Recommended for files 25 MB and above.

    Parameters
    ----------
    filename      : local path of the file to upload
    bucket_name   : destination S3 bucket
    object_name   : S3 key; defaults to the file's base name
    validate_mime : if True, validate MIME type before uploading
    """
    if object_name is None:
        object_name = filename.split("/")[-1]

    extra_args = {}
    if validate_mime:
        mime_type = validate_mime_type(filename)
        extra_args["ContentType"] = mime_type

    config = TransferConfig(
        multipart_threshold=1024 * 1024 * 25,   # trigger multipart at 25 MB
        max_concurrency=10,                      # parallel upload threads
        multipart_chunksize=1024 * 1024 * 25,   # each chunk = 25 MB
        use_threads=True,
    )

    aws_s3_client.upload_file(
        filename, bucket_name, object_name,
        Config=config,
        ExtraArgs=extra_args if extra_args else None,
    )
    print(f"  Uploaded (large/multipart): '{filename}' → s3://{bucket_name}/{object_name}")
    return True
