# AWS Bedrock Infrastructure Setup Scripts

This directory contains automation scripts for setting up the AWS infrastructure required for the Full Bedrock Agents migration.

## Prerequisites

1. **AWS Account**: You need an AWS account with appropriate permissions
2. **AWS CLI**: Install and configure AWS CLI
   ```bash
   aws configure
   ```
3. **Python 3.12+**: Required for running the scripts
4. **boto3**: AWS SDK for Python
   ```bash
   pip install boto3
   ```

## AWS Permissions Required

Your AWS credentials need the following permissions:
- `bedrock:*` - Full Bedrock access
- `s3:*` - S3 bucket creation and management
- `lambda:*` - Lambda function deployment
- `iam:*` - IAM role creation and policy management
- `aoss:*` - OpenSearch Serverless
- `logs:*` - CloudWatch Logs

## Scripts Overview

### 1. `setup_bedrock_agents.py`
Creates all Bedrock Agents (Supervisor and 4 Sub-Agents) with proper instructions and configurations.

**Usage:**
```bash
python setup_bedrock_agents.py --region us-east-1
```

**Output:**
- Creates 5 Bedrock Agents
- Generates `agent_config.json` with all agent IDs and ARNs

### 2. `setup_knowledge_base.py`
Sets up S3 bucket, OpenSearch Serverless collection, and Knowledge Base.

**Usage:**
```bash
python setup_knowledge_base.py --region us-east-1
```

**Output:**
- Creates S3 bucket `fundingforge-knowledge-base`
- Creates OpenSearch Serverless collection
- Creates Knowledge Base with data source
- Generates `knowledge_base_config.json`

### 3. `deploy_lambda_functions.py`
Deploys all Lambda Action Groups with OpenAPI schemas.

**Usage:**
```bash
python deploy_lambda_functions.py --region us-east-1
```

**Output:**
- Deploys 3 Lambda functions
- Creates IAM roles for Lambda execution
- Generates `lambda_config.json`

### 4. `link_action_groups.py`
Links Lambda Action Groups to Bedrock Agents.

**Usage:**
```bash
python link_action_groups.py --region us-east-1
```

**Prerequisites:**
- Requires `agent_config.json` and `lambda_config.json`

### 5. `setup_iam_roles.py`
Creates and configures all IAM roles with least-privilege policies.

**Usage:**
```bash
python setup_iam_roles.py --region us-east-1
```

**Output:**
- Creates IAM roles for all agents
- Attaches appropriate policies
- Generates `iam_config.json`

### 6. `run_all.py`
Master script that runs all setup scripts in the correct order.

**Usage:**
```bash
python run_all.py --region us-east-1
```

This is the recommended way to set up the entire infrastructure.

## Step-by-Step Setup

### Option A: Run Everything at Once (Recommended)
```bash
cd scripts/aws-setup
python run_all.py --region us-east-1
```

### Option B: Run Scripts Individually
```bash
# Step 1: Set up IAM roles first
python setup_iam_roles.py --region us-east-1

# Step 2: Set up Knowledge Base
python setup_knowledge_base.py --region us-east-1

# Step 3: Deploy Lambda functions
python deploy_lambda_functions.py --region us-east-1

# Step 4: Create Bedrock Agents
python setup_bedrock_agents.py --region us-east-1

# Step 5: Link Action Groups to Agents
python link_action_groups.py --region us-east-1
```

## Configuration Files Generated

After running the scripts, you'll have these configuration files:

- `agent_config.json` - Agent IDs and ARNs
- `knowledge_base_config.json` - Knowledge Base and S3 details
- `lambda_config.json` - Lambda function ARNs
- `iam_config.json` - IAM role ARNs
- `.env.aws` - Environment variables for Express backend

## Using the Configuration

Copy the generated `.env.aws` file to your project root and merge with your existing `.env`:

```bash
cat scripts/aws-setup/.env.aws >> .env
```

## Troubleshooting

### Permission Errors
If you get permission errors, ensure your AWS credentials have the required permissions listed above.

### Region Not Supported
Bedrock Agents are available in specific regions. Use `us-east-1` or `us-west-2`.

### Quota Limits
If you hit quota limits, request increases via AWS Service Quotas console.

### Agent Creation Fails
Check CloudWatch Logs for detailed error messages:
```bash
aws logs tail /aws/bedrock/agents --follow
```

## Cleanup

To delete all created resources:
```bash
python cleanup_all.py --region us-east-1 --confirm
```

**WARNING**: This will delete all agents, Lambda functions, S3 buckets, and IAM roles created by these scripts.

## Cost Estimation

Running these scripts will create resources with the following estimated costs:
- Bedrock Agents: Pay per invocation (~$0.01 per 1000 tokens)
- Knowledge Base: ~$0.10/hour for OpenSearch Serverless
- Lambda: Pay per invocation (free tier: 1M requests/month)
- S3: ~$0.023/GB/month

Estimated monthly cost for 1000 proposals: ~$220/month (optimized)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review CloudWatch Logs
3. Consult the design document: `.kiro/specs/full-bedrock-agents-migration/design.md`
