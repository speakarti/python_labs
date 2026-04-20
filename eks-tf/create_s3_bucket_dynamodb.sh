# Create S3 bucket for state
aws s3 mb s3://eks-np01-tfstate-744958734165 \
  --region us-east-1

# Enable versioning (important for state recovery)
aws s3api put-bucket-versioning \
  --bucket eks-np01-tfstate-744958734165 \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket eks-np01-tfstate-744958734165 \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket eks-np01-tfstate-744958734165 \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name eks-np01-tf-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

echo "✅ S3 bucket and DynamoDB table created!, Varifying next.."


# Verify bucket
aws s3 ls | grep eks-np01

# Verify DynamoDB
aws dynamodb describe-table \
  --table-name eks-np01-tf-lock \
  --region us-east-1 \
  --query "Table.{Name:TableName,Status:TableStatus}" \
  --output json