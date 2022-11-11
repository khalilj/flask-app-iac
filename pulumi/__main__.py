import pulumi_aws as aws
from ecs_app_deployer import EcsAppDeployer
from cloud_front_deployer import CloudFrontDeployer

ecr_repo = aws.ecr.Repository('flaskapp', name="flaskapp",
    image_tag_mutability="MUTABLE")

ecs_app_deployer = EcsAppDeployer('development')
ecs_app_deployer.create()

cloud_front_deployer = CloudFrontDeployer("salt-site", "salt-site", 'development')
cloud_front_deployer.create()