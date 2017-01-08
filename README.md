# ecs-host-service-scale

A Lambda function to ensure an ECS Service is set to the correct Desired Count for a One-Task-Per-Host placement value for any cluster that runs the Service.

## Requirements

- `boto3` (included in AWS Lambda functions, no need for packaged deployment)
- `ECS_SERVICE_ARN` environment variable
- IAM Role/Policy access setup

## Flow

![UML Sequence Flow](http://uml.mvnsearch.org/gist/00347bf8cfd22ac011f0e8f1bfa12359)

## Deployment

The function is meant to be deployed as a non-VPC Lambda function. It will probably work in a VPC environment, given an Internet Gateway and proper permissions, but it simply does not need access to any in-VPC resources, only AWS API calls.

- IAM Policy & IAM Role allowing: `ecs:Describe*` and `ecs:UpdateService`
- CloudWatch Event Rule for: `{"source": ["aws.ecs"], "detail-type": ["ECS Container Instance State Change"]}`
- Code from `lambda_function.py`
- The ECS Service ARN environment variable

## Testing

- Install all requirements via `pip install -r requirements.txt`
- Execute tests vis `pytest`

See [py.test docs](http://doc.pytest.org/) and [botocore Stubber](http://botocore.readthedocs.io/en/latest/reference/stubber.html) reference for more.

## Contributing

1. [Fork it](https://github.com/miketheman/ecs-host-service-scale/fork)
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Test your changes with `pytest --cov` - the tests currently cover the code 100% - don't lower that number!
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin my-new-feature`)
6. Create a new Pull Request

# Author

[Mike Fiedler](https://github.com/miketheman) (miketheman@gmail.com)
