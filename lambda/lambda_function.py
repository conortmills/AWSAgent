import os
import sys
import logging
from typing import Annotated

sys.path.append('lib')

from boto3.session import Session
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from aws_lambda_powertools.event_handler.bedrock_agent import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.event_handler.exceptions import BadRequestError

from neo4j_service import Neo4jService

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Lambda Powertools setup (we're initializing 2 resolvers here: one for AWS Bedrock agent requests and one for HTTP requests)
http_resolver = APIGatewayRestResolver(enable_validation = True)
bedrock_agent_resolver = BedrockAgentResolver()

# ------------ #
# MAIN HANDLER #
# ------------ #

def handler(event, context):
    logger.info(f"handler(): event = { event }")

    # Picking a resolver based on event type
    if 'agent' in event:
        logger.info("Bedrock request")
        Neo4jService.initialize()
        response = bedrock_agent_resolver.resolve(event, context)            
        Neo4jService.close()
        return response
    elif 'httpMethod' in event:
        logger.info("HTTP request")
        return http_resolver.resolve(event, context)    
    else:
        raise BadRequestError()

# ----------- #
# HTTP ROUTES #
# ----------- #

@http_resolver.get("/agent-smith")
def invoke_agent_smith():
    # Extract the prompt from the query string parameters
    prompt = http_resolver.current_event.query_string_parameters.get("prompt", "")
    logger.info(f"invoke_agent_smith(): prompt = { prompt }")
    
    if not prompt:
        return {
            "statusCode": 400,
            "body": "Prompt is required"
        }
    
    # Prepare the agent invocation parameters
    agent_id = http_resolver.environment_variables.get('AGENT_ID')
    agent_alias_id = http_resolver.environment_variables.get('AGENT_ALIAS_ID')
    
    if not agent_id or not agent_alias_id:
        return {
            "statusCode": 500,
            "body": "Agent ID and Alias ID must be configured in environment variables"
        }
    
    # Use the helper function (_invoke_agent) to invoke the agent
    try:
        response = _invoke_agent(prompt)  # Call _invoke_agent instead of invoke_bedrock_agent
        logger.info(f"Agent response: {response}")
        
        return {
            "statusCode": 200,
            "body": response
        }
    
    except Exception as e:
        logger.error(f"Error invoking agent: {e}")
        return {
            "statusCode": 500,
            "body": f"Error invoking agent: {str(e)}"
        }


def _invoke_agent(user_prompt):
    session = Session(
        aws_access_key_id = os.environ.get('IAM_ACCESS_KEY'),
        aws_secret_access_key = os.environ.get('IAM_SECRET_KEY'),
        region_name = 'ca-central-1',
    )

    client = session.client('bedrock-agent-runtime')
    invokeParams = {
        'agentId': os.environ.get('AGENT_ID'),
        'agentAliasId': os.environ.get('AGENT_ALIAS_ID'),
        'inputText': user_prompt,
        'sessionId': 'homework-session',
        'enableTrace': True,
    }

    if user_prompt == "exit":
        invokeParams['endSession'] = True

    logger.info(f"invoke_agent(): invokeParams = { invokeParams }")
    response = client.invoke_agent(**invokeParams)

    completion = ""
    final_response = ""

    for event in response.get("completion"):
        if "trace" in event:
            logger.info(f"invoke_agent(): trace = {event['trace']}")
            
        if "chunk" in event:
            chunk = event["chunk"]
            chunk_content = chunk["bytes"].decode()
            completion += chunk_content
            final_response = completion
            logger.info(f"invoke_agent(): final_response = {final_response}")

            if final_response == "Session is terminated as 'endSession' flag is set in request.":
                return "Session terminated."

            return final_response    
    return "error"

# ------------------------- #
# OPENAPI SCHEMA GENERATION #
# ------------------------- #

if __name__ == "__main__":  
    print(bedrock_agent_resolver.get_openapi_json_schema())