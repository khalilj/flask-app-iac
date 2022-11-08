import pulumi_aws as aws

foo = aws.ecr.Repository('flaskapp', name="flaskapp",
    image_tag_mutability="MUTABLE")