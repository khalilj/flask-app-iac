import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

ecr_repo = aws.ecr.Repository('flaskapp', name="flaskapp",
    image_tag_mutability="MUTABLE")

vpc = awsx.ec2.Vpc("dev")
flaskAppsecurityGroup = aws.ec2.SecurityGroup("flask-app-secgrp", vpc_id=vpc.vpc_id)
cluster = aws.ecs.Cluster("dev-cluster", name="dev-cluster")
lb = awsx.lb.ApplicationLoadBalancer("flask-app-lb", 
        subnet_ids=vpc.private_subnet_ids,
        default_target_group=aws.lb.TargetGroup('flask-app-lb-rg',
            port=80,
            protocol="HTTP",
            target_type="ip",
            vpc_id=vpc.vpc_id
        ))
service = awsx.ecs.FargateService("flask-app",
    cluster=cluster.arn,
    desired_count=2,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=vpc.private_subnet_ids,
        security_groups=[flaskAppsecurityGroup.id]
    ),
    task_definition_args=awsx.ecs.FargateServiceTaskDefinitionArgs(
        # task_role=awsx.DefaultRoleWithPolicyArgs(
        #     role_arn='arn:aws:iam::821594384510:role/ecsTaskExecutionRole'),
        container=awsx.ecs.TaskDefinitionContainerDefinitionArgs(
            image="nginx:latest",
            cpu=512,
            memory=128,
            essential=True,
            port_mappings=[awsx.ecs.TaskDefinitionPortMappingArgs(
                target_group=lb.default_target_group
            )],
        )
    )
)

pulumi.export('url', lb.load_balancer.dns_name)

bucket_name = "salt-site"
site_bucket = aws.s3.Bucket(bucket_name, bucket=bucket_name,
    acl="public-read",
    tags={
        "Environment": "Dev",
        "Name": bucket_name,
    })

s3_origin_id = "salt-site-s3"
s3_distribution = aws.cloudfront.Distribution("salt-site",
    origins=[aws.cloudfront.DistributionOriginArgs(
        domain_name=site_bucket.bucket_regional_domain_name,
        origin_id=s3_origin_id
    )],
    enabled=True,
    comment="Salt portal",
    default_root_object="index.html",
    tags={
        "Environment": "Dev",
    },
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        allowed_methods=[
            "DELETE",
            "GET",
            "HEAD",
            "OPTIONS",
            "PATCH",
            "POST",
            "PUT",
        ],
        cached_methods=[
            "GET",
            "HEAD",
        ],
        target_origin_id=s3_origin_id,
        forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=False,
            cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="none",
            ),
        ),
        viewer_protocol_policy="allow-all",
        min_ttl=0,
        default_ttl=3600,
        max_ttl=86400,
    ),
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none",
            locations=[
            ],
        ),
    ),
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True,
    )
)