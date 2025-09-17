import json
from prefect import flow, task
from s3fs import S3FileSystem

@task
def generate_data():
    """Generate sample data for testing."""
    data = [{"id": i, "name": f"item_{i}"} for i in range(10)]
    return data

@task
def save_to_rustfs(data: list):
    """Save data to RustFS S3-compatible object storage."""
    s3 = S3FileSystem(
        key='rustfsadmin',
        secret='rustfsadmin',
        client_kwargs={'endpoint_url': 'http://rustfs:9000'}
    )

    bucket_name = 'prefect-data'
    path = f"{bucket_name}/sample_data.json"

    if not s3.exists(bucket_name):
        s3.mkdir(bucket_name)

    # Write data to S3
    with s3.open(path, 'w') as f:
        json.dump(data, f)

    return f"Data saved to {path}"

@flow(name="simple_rustfs_integration_flow")
def main_flow():
    """Main Prefect flow for RustFS integration."""
    data = generate_data()
    result = save_to_rustfs(data)
    print(result)

if __name__ == "__main__":
    main_flow()
