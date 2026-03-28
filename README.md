## Catch-UP

### Try to run help command:
```python
python main.py -h
```

---

## Task 1 — New Features

### Setup

1. Install dependencies:
```bash
pip install boto3 python-dotenv
```

2. Copy and fill in credentials:
```bash
cp .env.example .env
```

---

### Upload a small file (single-part)
Best for files **under 25 MB**. Uses boto3's standard `upload_file()`.

```bash
# short
python main.py -bn my-bucket -uf -fp ./photo.jpg

# long
python main.py --bucket_name my-bucket --upload_file --file_path ./photo.jpg
```

---

### Upload a small file with MIME type validation *(optional)*
Validates the file extension against an allow-list before uploading.
Allowed types: `image/jpeg`, `image/png`, `image/gif`, `image/webp`,
`application/pdf`, `text/plain`, `text/csv`, `application/zip`, `application/json`

```bash
python main.py -bn my-bucket -uf -fp ./photo.jpg -vm
```

---

### Upload a large file (multipart)
Best for files **25 MB and above**. Uses `TransferConfig` to split the file
into 25 MB chunks and upload them with 10 parallel threads. S3 assembles
the chunks server-side on completion.

```bash
# short
python main.py -bn my-bucket -ulf -fp ./bigvideo.mp4

# long
python main.py --bucket_name my-bucket --upload_large_file --file_path ./bigvideo.mp4
```

---

### Upload a large file with MIME type validation *(optional)*
```bash
python main.py -bn my-bucket -ulf -fp ./bigvideo.mp4 -vm
```

---

### Set lifecycle policy — auto-delete after 120 days
Attaches an S3 lifecycle rule that automatically deletes **all objects**
in the bucket 120 days after their creation date.

```bash
# short
python main.py -bn my-bucket -lcp

# long
python main.py --bucket_name my-bucket --lifecycle_policy
```

---


## Task 2 — Delete Object

### Delete a specific object from a bucket
Deletes a single object identified by its key (file name) from the bucket.
```bash
python main.py -bn my-bucket -del -fn photo.jpg
```

---

## Task 3 — Versioning

### Check if versioning is enabled on a bucket
```bash
python main.py -bn my-bucket -bv
```
Output example: `Versioning status for 'my-bucket': Enabled`

---

### List all versions of a file
Shows the number of versions, each version ID, and its creation date.
```bash
python main.py -bn my-bucket -lv -fn photo.jpg
```

---

### Restore the previous version of a file
Copies the previous version on top of the current one, making it the new latest version.
```bash
python main.py -bn my-bucket -rv -fn photo.jpg
```

---

## Project structure

```
.
├── auth.py                  # AWS client init (reads .env)
├── main.py                  # CLI entry point (argparse)
├── bucket/
│   ├── crud.py              # create / delete / list / check buckets
│   ├── policy.py            # read & assign bucket policies
│   ├── encryption.py        # enable & read bucket encryption
│   └── lifecycle.py         # lifecycle policy (auto-delete) ← NEW
├── object/
│   ├── crud.py              # upload small/large, list, download ← UPDATED
│   └── policy.py            # set object ACL
└── .env.example
```

---

## Changes vs original catch-up script

| File | Change |
|------|--------|
| `object/crud.py` | Fixed broken `upload_file()`, added `upload_large_file()`, added `validate_mime_type()` |
| `bucket/lifecycle.py` | New file — `set_lifecycle_policy()` |
| `bucket/versioning.py` | New file — `get_bucket_versioning()`, `list_object_versions()`, `restore_previous_version()` |
| `main.py` | Added `-uf`, `-ulf`, `-fp`, `-vm`, `-lcp`, `-del`, `-fn`, `-bv`, `-lv`, `-rv` arguments and handlers |
| `README.md` | Updated with full documentation |
