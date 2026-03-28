def get_bucket_versioning(aws_s3_client, bucket_name):
    """
    Check whether versioning is enabled on a bucket.

    Returns the versioning status: 'Enabled', 'Suspended', or 'Disabled'.
    """
    response = aws_s3_client.get_bucket_versioning(Bucket=bucket_name)
    status = response.get("Status", "Disabled")
    print(f"  Versioning status for '{bucket_name}': {status}")
    return status


def list_object_versions(aws_s3_client, bucket_name, object_key):
    """
    List all versions of a specific object, showing version ID and creation date.

    Parameters
    ----------
    bucket_name : the S3 bucket
    object_key  : the file name / key to list versions for
    """
    response = aws_s3_client.list_object_versions(
        Bucket=bucket_name,
        Prefix=object_key,
    )
    versions = response.get("Versions", [])

    if not versions:
        print(f"  No versions found for '{object_key}' in bucket '{bucket_name}'.")
        return []

    print(f"  Found {len(versions)} version(s) of '{object_key}':")
    for i, v in enumerate(versions):
        latest = " ← latest" if v.get("IsLatest") else ""
        print(f"    [{i}] VersionId: {v['VersionId']}  |  Created: {v['LastModified']}{latest}")

    return versions


def restore_previous_version(aws_s3_client, bucket_name, object_key):
    """
    Restore the previous version of an object by copying it as the new current version.

    How it works:
      1. List all versions of the object (sorted newest first by S3)
      2. Pick the second entry — that is the previous version
      3. Copy it on top of itself without a VersionId → becomes the new latest version

    Parameters
    ----------
    bucket_name : the S3 bucket
    object_key  : the file name / key to restore
    """
    response = aws_s3_client.list_object_versions(
        Bucket=bucket_name,
        Prefix=object_key,
    )
    versions = response.get("Versions", [])

    if len(versions) < 2:
        print(f"  No previous version found for '{object_key}'. Need at least 2 versions.")
        return False

    # S3 returns versions newest-first; index 0 = current, index 1 = previous
    previous_version = versions[1]
    version_id = previous_version["VersionId"]
    created = previous_version["LastModified"]

    print(f"  Restoring previous version: {version_id} (created {created})")

    aws_s3_client.copy_object(
        Bucket=bucket_name,
        CopySource={
            "Bucket": bucket_name,
            "Key": object_key,
            "VersionId": version_id,
        },
        Key=object_key,
    )

    print(f"  '{object_key}' has been restored to its previous version successfully.")
    return True
