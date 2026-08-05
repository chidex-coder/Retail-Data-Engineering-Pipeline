#!/bin/bash
echo "Creating S3 bucket in LocalStack..."
awslocal s3 mb s3://retail-flow-bucket
awslocal s3 ls