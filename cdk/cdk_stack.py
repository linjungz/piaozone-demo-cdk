from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import (core, aws_ec2 as ec2, aws_ecs as ecs, aws_ecr as ecr, aws_iam as iam,
                     aws_ecs_patterns as ecs_patterns)


class kdECSDemo(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 建VPC与ECS Cluster
        # TODO: 即使指定 max_azs, 也只能部署2个AZ
        vpc = ec2.Vpc(self, "ECSVPC", cidr='10.0.0.0/16') 
        cluster = ecs.Cluster(self, "ECSCluster", vpc=vpc)

        #建Task Definition
        task_definition = ecs.FargateTaskDefinition(self, "ECSDemoTaskDefinition",
            task_role=iam.Role.from_role_arn(self, "fargate_task_role", "arn:aws-cn:iam::402202783068:role/ECS-Task-Role-Firelens"),
            execution_role=iam.Role.from_role_arn(self, "fargate_task_execution_role", "arn:aws-cn:iam::402202783068:role/ecsTaskExecutionRole")
        )

        task_definition.add_volume(name="data")

        # App Container
        app_container = task_definition.add_container(
            "AppContainer",
            image=ecs.ContainerImage.from_ecr_repository(
                ecr.Repository.from_repository_name(self, id="app-file-image", repository_name="app-file")
            ),            
            logging=ecs.FireLensLogDriver()
        )

        app_container.add_mount_points(ecs.MountPoint(
            container_path="/data/logs",
            read_only=False,
            source_volume="data"
        ))

        # app_container.add_port_mappings(ecs.PortMapping(container_port=80))
        
        # Log Router
        fluentbit_container = ecs.FirelensLogRouter(self, "fluentbit_container",
            firelens_config=ecs.FirelensConfig(
                type=ecs.FirelensLogRouterType.FLUENTBIT,
                options=ecs.FirelensOptions(
                    config_file_value="/extra.conf"
                )
            ),
            task_definition=task_definition,
            image=ecs.ContainerImage.from_ecr_repository(
                ecr.Repository.from_repository_name(self, id="log-router", repository_name="firelens-file")
            ),
            logging=ecs.AwsLogDriver(stream_prefix="/ecs/firelens-fluentbit-demo/")
        )
        
        fluentbit_container.add_mount_points(ecs.MountPoint(
            container_path="/data/logs",
            read_only=False,
            source_volume="data"
        ))

        # #建Service
        # ecs_patterns.ApplicationLoadBalancedFargateService(self, "ServiceWithLogging",
        #     cluster=cluster,
        #     desired_count=1,            # Default is 1
        #     task_definition=task_definition,
        #     public_load_balancer=True)  # Default is False

        






