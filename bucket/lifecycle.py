def set_lifecycle_policy(aws_s3_client, bucket_name, days=120):
    """
    Attach a lifecycle rule that automatically deletes every object
    in the bucket after `days` days from the date of creation.

    Parameters
    ----------
    bucket_name : target S3 bucket
    days        : retention period in days (default: 120)
    """
    lifecycle_config = {
        "Rules": [
            {
                "ID": f"DeleteAfter{days}Days",
                "Status": "Enabled",
                "Filter": {"Prefix": ""},   # applies to ALL objects
                "Expiration": {"Days": days},
            }
        ]
    }
    response = aws_s3_client.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration=lifecycle_config,
    )
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 200:
        print(f"  Lifecycle policy set on '{bucket_name}': objects deleted after {days} days.")
        return True
    return False
