import pulumi_aws as aws
from pulumi import export, ResourceOptions
import json

class EcsAppDeployer:
    def __init__(self, clsuetr_name):
        self.clsuetr_name = clsuetr_name
    
    def create(self):
        cluster = aws.ecs.Cluster(self.clsuetr_name)
        default_vpc = aws.ec2.get_vpc(default=True)
        default_vpc_subnets = aws.ec2.get_subnet_ids(vpc_id=default_vpc.id)

        # Create a SecurityGroup that permits HTTP ingress and unrestricted egress.
        web_security_group = aws.ec2.SecurityGroup('web-secgrp',
            vpc_id=default_vpc.id,
            description='Enable HTTP access',
            ingress=[aws.ec2.SecurityGroupIngressArgs(
                protocol='tcp',
                from_port=80,
                to_port=80,
                cidr_blocks=['0.0.0.0/0'],
            )],
            egress=[aws.ec2.SecurityGroupEgressArgs(
                protocol='-1',
                from_port=0,
                to_port=0,
                cidr_blocks=['0.0.0.0/0'],
            )],
        )

        # Create a load balancer to listen for HTTP traffic on port 80.
        alb = aws.lb.LoadBalancer('flask-app-lb',
            security_groups=[web_security_group.id],
            subnets=default_vpc_subnets.ids,
        )

        atg = aws.lb.TargetGroup('flask-app-tg',
            port=80,
            protocol='HTTP',
            target_type='ip',
            vpc_id=default_vpc.id,
        )

        wl = aws.lb.Listener('web',
            load_balancer_arn=alb.arn,
            port=80,
            default_actions=[aws.lb.ListenerDefaultActionArgs(
                type='forward',
                target_group_arn=atg.arn,
            )],
        )

        # Create an IAM role that can be used by our service's task.
        role = aws.iam.Role('task-exec-role',
            assume_role_policy=json.dumps({
                'Version': '2008-10-17',
                'Statement': [{
                    'Sid': '',
                    'Effect': 'Allow',
                    'Principal': {
                        'Service': 'ecs-tasks.amazonaws.com'
                    },
                    'Action': 'sts:AssumeRole',
                }]
            }),
        )

        rpa = aws.iam.RolePolicyAttachment('task-exec-policy',
            role=role.name,
            policy_arn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
        )

        # Spin up a load balanced service running our container image.
        task_definition = aws.ecs.TaskDefinition('flask-app-task',
            family='fargate-task-definition',
            cpu='256',
            memory='512',
            network_mode='awsvpc',
            requires_compatibilities=['FARGATE'],
            execution_role_arn=role.arn,
            container_definitions=json.dumps([{
                'name': 'flask-app',
                'image': '821594384510.dkr.ecr.us-east-1.amazonaws.com/flaskapp:054cf69',
                'portMappings': [{
                    'containerPort': 80,
                    'hostPort': 80,
                    'protocol': 'tcp'
                }]
            }])
        )

        service = aws.ecs.Service('flask-app-svc',
            cluster=cluster.arn,
            desired_count=3,
            launch_type='FARGATE',
            task_definition=task_definition.arn,
            network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                assign_public_ip=True,
                subnets=default_vpc_subnets.ids,
                security_groups=[web_security_group.id],
            ),
            load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
                target_group_arn=atg.arn,
                container_name='flask-app',
                container_port=80,
            )],
            opts=ResourceOptions(depends_on=[wl]),
        )

        export('url', alb.dns_name)