# Promote AMI GitHub Action

The purpose of this action is to promote AMIs from a release candidate status to a production status. The action can also modify the AMI so that it is accessible from multiple AWS accounts.

## Usage

This action is typically used in the deployment part of a workflow. It assumes that an AMI was created earlier in the workflow and this AMI was tagged as a release candidate. 

### Example workflow

```yaml
name: My Workflow
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Promote AMI
      uses: exosite/ops-github-promote-ami@master

      with:
        ami_name_pattern: 'SERVICE-LINUX-NODE-ubuntu18.04-*'
        pr_number: '5'
        aws_region: 'us-west-2'
        aws_owner_account: '1892371923812'
        aws_additional_accounts: ['289348209384234', '198239174992123']
        aws_access_key: ${{ secret }}
        aws_secret_key: ${{ secret }}


```

### Inputs

| Input                                             | Description                                        |
|------------------------------------------------------|-----------------------------------------------|
| `ami_name_pattern`                     | A pattern which matches the AMI name   |
| `aws_additional_accounts` (optional)_  | A list of additional AWS accounts which need access to the AMI |
| `aws_region`                           | The AWS region where the AMI is located |
| `aws_owner_account`                    | The AWS account which owns the AMI      |
| `aws_access_key`                       | An AWS access key credential            |
| `aws_secret_key`                       | An AWS secret access key credential     |
| `aws_role_arn` _(optional)_            | An optional AWS role to assume          | 
| `pr_number`                            | The GitHub PR number associated with the AMI build |

### Outputs

| Output                                             | Description                                        |
|------------------------------------------------------|-----------------------------------------------|
| `ami_id`   | The ID of the AMI which was promoted    |
| `ami_name` | The name of the AMI which was promoted |

### Using outputs

Show people how to use your outputs in another action.

```yaml
steps:
- uses: actions/checkout@master
- name: Run action
  id: promote
  uses: exosite/ops-github-promote-ami@master

  with:
    ami_name_pattern: 'SERVICE-LINUX-NODE-ubuntu18.04-*'
    pr_number: '5'
    aws_region: 'us-west-2'
    aws_owner_account: '1892371923812'
    aws_additional_accounts: ['289348209384234', '198239174992123']
    aws_access_key: ${{ secret }}
    aws_secret_key: ${{ secret }}

- name: View outputs
    run: |
      echo "${{ steps.promote.outputs.ami_name }}"
```