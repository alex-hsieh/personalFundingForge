# Quick Start Guide - AWS Infrastructure Setup

This guide will help you set up the complete AWS infrastructure for the Bedrock Agents migration in about 15-20 minutes.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Python 3.12+** installed
4. **boto3** installed

## Step 1: Install Dependencies

```bash
cd scripts/aws-setup
pip install -r requirements.txt
```

## Step 2: Configure AWS Credentials

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (use `us-east-1` or `us-west-2`)
- Default output format (use `json`)

## Step 3: Run the Master Setup Script

```bash
python run_all.py --region us-east-1
```

This will:
- Create all IAM roles
- Set up S3 bucket and OpenSearch Serverless
- Create Knowledge Base with sample documents
- Deploy 3 Lambda functions
- Create 5 Bedrock Agents
- Link Action Groups to Agents
- Generate `.env.aws` file

**Estimated time:** 15-20 minutes

## Step 4: Review Generated Configuration

Check the generated files:

```bash
ls -la *.json
cat .env.aws
```

You should see:
- `iam_config.json` - IAM role ARNs
- `knowledge_base_config.json` - KB and S3 details
- `lambda_config.json` - Lambda function ARNs
- `agent_config.json` - Bedrock Agent IDs
- `action_groups_config.json` - Linked action groups
- `.env.aws` - Environment variables

## Step 5: Add AWS Credentials to .env.aws

Edit `.env.aws` and add your credentials:

**Option 1: Use AWS CLI Profile (Recommended for local dev)**
```bash
AWS_PROFILE=your-profile-name
```

**Option 2: Use Explicit Credentials**
```bash
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

## Step 6: Copy to Project Root

```bash
cat .env.aws >> ../../.env
```

## Step 7: Test the Setup

Test the Supervisor Agent via AWS CLI:

```bash
# Get agent ID from agent_config.json
AGENT_ID=$(jq -r '.agents.supervisor.id' agent_config.json)
ALIAS_ID=$(jq -r '.agents.supervisor.alias_id' agent_config.json)

# Test invocation
aws bedrock-agent-runtime invoke-agent \
  --agent-id $AGENT_ID \
  --agent-alias-id $ALIAS_ID \
  --session-id test-session-$(date +%s) \
  --input-text "Test the agent pipeline" \
  --region us-east-1 \
  output.txt

cat output.txt
```

## Step 8: Start Developer B Tasks

Now you can start implementing the Express backend integration:

```bash
cd ../../
# Install AWS SDK
npm install @aws-sdk/client-bedrock-agent-runtime

# Start refactoring agent-client.ts
# See: .kiro/specs/full-bedrock-agents-migration/tasks.md
```

## Troubleshooting

### Permission Errors

If you get permission errors, ensure your AWS user/role has these permissions:
- `bedrock:*`
- `s3:*`
- `lambda:*`
- `iam:*`
- `aoss:*`
- `logs:*`

### Region Not Supported

Bedrock Agents are available in specific regions. Use:
- `us-east-1` (recommended)
- `us-west-2`

### Script Fails Midway

You can re-run individual scripts:

```bash
# Re-run specific step
python setup_bedrock_agents.py --region us-east-1

# Or skip completed steps
python run_all.py --region us-east-1 --skip-kb
```

### Agent Creation Takes Too Long

Agent creation and preparation can take 5-10 minutes. The scripts include wait times, but you may need to wait longer for agents to become fully active.

### Knowledge Base Ingestion Fails

Check the ingestion job status:

```bash
KB_ID=$(jq -r '.knowledge_base.id' knowledge_base_config.json)
DS_ID=$(jq -r '.knowledge_base.data_source_id' knowledge_base_config.json)

aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --region us-east-1
```

## Cleanup

To delete all created resources:

```bash
python cleanup_all.py --region us-east-1 --confirm
```

**WARNING:** This will delete everything created by the setup scripts.

## Cost Monitoring

Monitor your AWS costs:

```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

Expected costs:
- Development/Testing: ~$10-20/month
- Production (1000 proposals/month): ~$220/month

## Next Steps

1. ✅ AWS Infrastructure complete
2. ⏭️ Implement Developer B tasks (Express backend)
3. ⏭️ Integration testing
4. ⏭️ Deploy to staging
5. ⏭️ Production rollout

See the full implementation plan: `.kiro/specs/full-bedrock-agents-migration/tasks.md`
