from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_logs as logs,
    Stack,
    Duration,
    RemovalPolicy
)
from constructs import Construct
from cdklabs.generative_ai_cdk_constructs.bedrock import (
    ActionGroupExecutor,
    Agent,
    AgentActionGroup,
    ApiSchema,
    BedrockFoundationModel,
)

class HomeworkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda setup
        agent_smith_lambda = _lambda.Function(
            self,
            'agent-smith-lambda',
            function_name = 'agent-smith-lambda',
            runtime = _lambda.Runtime.PYTHON_3_12,
            timeout = Duration.minutes(1),
            code = _lambda.Code.from_asset('../lambda', exclude=[".venv/**/*"]),
            handler = 'lambda_function.handler',
            layers = [
                    _lambda.LayerVersion.from_layer_version_arn(self, "Powertools for AWS Lambda", "arn:aws:lambda:ca-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:71"),
                ],
            log_group = logs.LogGroup(
                self,
                "agent-smith-lambda-log-group",
                retention = logs.RetentionDays.TWO_WEEKS,
                log_group_name = 'agent-smith-lambda',
                removal_policy = RemovalPolicy.DESTROY,
            ),
            # ...
        )    

        # API gateway setup
        api = apigw.RestApi(
            self,
            'rivio-homework-api',
            deploy_options = apigw.StageOptions(
                stage_name = "homework",
                logging_level = apigw.MethodLoggingLevel.INFO,
                data_trace_enabled = True,
                tracing_enabled = True,

            ),
            rest_api_name = "rivio-homework-api",
            cloud_watch_role = True,
        )

        root_resource = api.root.add_resource('agent-smith')

        # ...

        # Bedrock agent setup        
        agent = Agent(
            self,
            "agent-smith-homework",
            foundation_model = BedrockFoundationModel.ANTHROPIC_CLAUDE_SONNET_V1_0,
            instruction = """
                You are a helpful assistant that can retrieve information on purchase orders.
            """,
            name = "agent-smith-homework",
            user_input_enabled = True,
            should_prepare_agent = True,
        )

        executor_group = ActionGroupExecutor.fromlambda_function(agent_smith_lambda)
        action_group = AgentActionGroup(
            name = "agent-smith-actions",
            description = "Use these functions to fetch information on suppliers and parts",
            executor = executor_group,
            enabled = True,
            api_schema = ApiSchema.from_local_asset("../lambda/openapi_schema.json"), 
        )
        agent.add_action_group(action_group)