import logging
from botocore.exceptions import ClientError
from auth import init_client
from bucket.crud import list_buckets, create_bucket, delete_bucket, bucket_exists
from bucket.policy import read_bucket_policy, assign_policy
from bucket.lifecycle import set_lifecycle_policy
from object.crud import (
    download_file_and_upload_to_s3,
    get_objects,
    upload_file,
    upload_large_file,
    delete_object,
)
from bucket.encryption import set_bucket_encryption, read_bucket_encryption
import argparse

parser = argparse.ArgumentParser(
    description="CLI program that helps with S3 buckets.",
    usage="""
    How to download and upload directly:
    short:
        python main.py -bn new-bucket-btu-7 -ol https://cdn.activestate.com/wp-content/uploads/2021/12/python-coding-mistakes.jpg -du
    long:
       python main.py  --bucket_name new-bucket-btu-7 --object_link https://cdn.activestate.com/wp-content/uploads/2021/12/python-coding-mistakes.jpg --download_upload

    How to list buckets:
    short:
        python main.py -lb
    long:
        python main.py --list_buckets

    How to create bucket:
    short:
        -bn new-bucket-btu-1 -cb -region us-west-2
    long:
        --bucket_name new-bucket-btu-1 --create_bucket --region us-west-2

    How to assign missing policy:
    short:
        -bn new-bucket-btu-1 -amp
    long:
        --bn new-bucket-btu-1 --assign_missing_policy

    How to upload a small file (single-part):
        python main.py -bn my-bucket -uf -fp ./photo.jpg
        python main.py -bn my-bucket -uf -fp ./photo.jpg -vm    (+ MIME validation)

    How to upload a large file (multipart):
        python main.py -bn my-bucket -ulf -fp ./bigvideo.mp4
        python main.py -bn my-bucket -ulf -fp ./bigvideo.mp4 -vm  (+ MIME validation)

    How to set lifecycle policy (auto-delete objects after 120 days):
        python main.py -bn my-bucket -lcp

    How to delete a specific object from a bucket:
        python main.py -bn my-bucket -del -fn photo.jpg
    """,
    prog="main.py",
    epilog="DEMO APP FOR BTU_AWS",
)

# ── original arguments (preserved exactly) ──────────────────────────────────

parser.add_argument(
    "-lb",
    "--list_buckets",
    help="List already created buckets.",
    action="store_true",
)

parser.add_argument(
    "-cb",
    "--create_bucket",
    help="Flag to create bucket.",
    choices=["False", "True"],
    type=str,
    nargs="?",
    # https://jdhao.github.io/2018/10/11/python_argparse_set_boolean_params
    const="True",
    default="False",
)

parser.add_argument(
    "-bn", "--bucket_name", type=str, help="Pass bucket name.", default=None
)

parser.add_argument(
    "-bc",
    "--bucket_check",
    help="Check if bucket already exists.",
    choices=["False", "True"],
    type=str,
    nargs="?",
    const="True",
    default="True",
)

parser.add_argument(
    "-region", "--region", type=str, help="Region variable.", default=None
)

parser.add_argument(
    "-db",
    "--delete_bucket",
    help="flag to delete bucket",
    choices=["False", "True"],
    type=str,
    nargs="?",
    const="True",
    default="False",
)

parser.add_argument(
    "-be",
    "--bucket_exists",
    help="flag to check if bucket exists",
    choices=["False", "True"],
    type=str,
    nargs="?",
    const="True",
    default="False",
)

parser.add_argument(
    "-rp",
    "--read_policy",
    help="flag to read bucket policy.",
    choices=["False", "True"],
    type=str,
    nargs="?",
    const="True",
    default="False",
)

parser.add_argument(
    "-arp",
    "--assign_read_policy",
    help="flag to assign read bucket policy.",
    choices=["False", "True"],
    type=str,
    nargs="?",
    const="True",
    default="False",
)

parser.add_argument(
    "-amp",
    "--assign_missing_policy",
    help="flag to assign read bucket policy.",
    choices=["False", "True"],
    type=str,
    nargs="?",
    const="True",
    default="False",
)

parser.add_argument(
    "-du",
    "--download_upload",
    choices=["False", "True"],
    help="download and upload to bucket",
    type=str,
    nargs="?",
    const="True",
    default="False",
)

parser.add_argument(
    "-ol",
    "--object_link",
    type=str,
    help="link to download and upload to bucket",
    default=None,
)

parser.add_argument(
    "-lo",
    "--list_objects",
    type=str,
    help="list bucket object",
    nargs="?",
    const="True",
    default="False",
)

parser.add_argument(
    "-ben",
    "--bucket_encryption",
    type=str,
    help="bucket object encryption",
    nargs="?",
    const="True",
    default="False",
)

parser.add_argument(
    "-rben",
    "--read_bucket_encryption",
    type=str,
    help="list bucket object",
    nargs="?",
    const="True",
    default="False",
)

# ── NEW arguments ────────────────────────────────────────────────────────────

parser.add_argument(
    "-fp",
    "--file_path",
    type=str,
    help="Local path of the file to upload. Required when using -uf or -ulf.",
    default=None,
)

parser.add_argument(
    "-vm",
    "--validate_mime",
    help="Optionally validate the file MIME type before uploading.",
    action="store_true",
)

parser.add_argument(
    "-uf",
    "--upload_file",
    type=str,
    help="Upload a small file to S3 using single-part upload. Requires -fp.",
    nargs="?",
    const="True",
    default="False",
)

parser.add_argument(
    "-ulf",
    "--upload_large_file",
    type=str,
    help="Upload a large file to S3 using multipart upload. Requires -fp.",
    nargs="?",
    const="True",
    default="False",
)

parser.add_argument(
    "-lcp",
    "--lifecycle_policy",
    type=str,
    help="Set a lifecycle policy: auto-delete all objects after 120 days.",
    nargs="?",
    const="True",
    default="False",
)



parser.add_argument(
    "-fn",
    "--file_name",
    type=str,
    help="The key (file name) of the object in S3. Used with -del.",
    default=None,
)

parser.add_argument(
    "-del",
    "--delete_object",
    type=str,
    help="Delete a specific object from the bucket by its key. Requires -bn and -fn.",
    nargs="?",
    const="True",
    default="False",
)

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    s3_client = init_client()
    args = parser.parse_args()

    if args.bucket_name:
        if args.create_bucket == "True":
            if not args.region:
                parser.error("Please provide region for bucket --region REGION_NAME")
            if (args.bucket_check == "True") and bucket_exists(
                s3_client, args.bucket_name
            ):
                parser.error("Bucket already exists")
            if create_bucket(s3_client, args.bucket_name, args.region):
                print("Bucket successfully created")

        if (args.delete_bucket == "True") and delete_bucket(
            s3_client, args.bucket_name
        ):
            print("Bucket successfully deleted")

        if args.bucket_exists == "True":
            print(f"Bucket exists: {bucket_exists(s3_client, args.bucket_name)}")

        if args.read_policy == "True":
            print(read_bucket_policy(s3_client, args.bucket_name))

        if args.assign_read_policy == "True":
            assign_policy(s3_client, "public_read_policy", args.bucket_name)

        if args.assign_missing_policy == "True":
            assign_policy(s3_client, "multiple_policy", args.bucket_name)

        if args.object_link:
            if args.download_upload == "True":
                print(
                    download_file_and_upload_to_s3(
                        s3_client, args.bucket_name, args.object_link
                    )
                )

        if args.bucket_encryption == "True":
            if set_bucket_encryption(s3_client, args.bucket_name):
                print("Encryption set")

        if args.read_bucket_encryption == "True":
            print(read_bucket_encryption(s3_client, args.bucket_name))

        if args.list_objects == "True":
            get_objects(s3_client, args.bucket_name)

        # ── NEW: upload small file (single-part) ────────────────────────────
        if args.upload_file == "True":
            if not args.file_path:
                parser.error("-uf / --upload_file requires -fp / --file_path")
            upload_file(
                s3_client,
                args.file_path,
                args.bucket_name,
                validate_mime=args.validate_mime,
            )

        # ── NEW: upload large file (multipart) ──────────────────────────────
        if args.upload_large_file == "True":
            if not args.file_path:
                parser.error("-ulf / --upload_large_file requires -fp / --file_path")
            upload_large_file(
                s3_client,
                args.file_path,
                args.bucket_name,
                validate_mime=args.validate_mime,
            )

        # ── NEW: lifecycle policy (delete after 120 days) ───────────────────
        if args.lifecycle_policy == "True":
            set_lifecycle_policy(s3_client, args.bucket_name, days=120)


        # ── NEW: delete object ───────────────────────────────────────────────
        if args.delete_object == "True":
            if not args.file_name:
                parser.error("-del / --delete_object requires -fn / --file_name")
            delete_object(s3_client, args.bucket_name, args.file_name)
    if args.list_buckets:
        buckets = list_buckets(s3_client)
        if buckets:
            for bucket in buckets["Buckets"]:
                print(f'  {bucket["Name"]}')


if __name__ == "__main__":
    try:
        main()
    except ClientError as e:
        logging.error(e)
