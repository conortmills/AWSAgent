
# Rivio Homework

## Foreword

Hello!

Thank you for taking the time to go through this homework.

I created this exercise because I don't believe in leetcode-style coding interviews. I don't care if you don't remember how to implement a binary search tree. What I care about is your ability to problem-solve something you're not familiar with, because that's what you'll be doing every day at Rivio.

I've split this exercise in 3 parts:
1. Infrastructure as code (using CDK) to set up a small AWS stack powering an AI agent
2. Unstructured to structured data (PDF file to Neo4j graph)
3. Providing our agent with a tool

You won't be coding from scratch, and will be guided along the way. Look for `# ...` comments, which indicate where you should add code.

**IMPORTANT:** This is a timed exercise, one I would expect completed in 5h or less. **You will lose access to the repository on the 5-hour mark**. These expectations are only realistic if you get help from an AI assistant. We use Cursor, and I highly recommend you use it too (or another AI-powered IDE).

Good luck, I'm looking forward to seeing your work!

Leo

# Part 1: Infrastructure as code

In this part you'll get to create Agent Smith, a simplified version of one of Rivio's agents. You'll edit AWS CDK code to set up the required infrastructure, as well as a Python lambda to make the agent accessible through an HTTP endpoint.

## Pre-requisites

[Install the AWS CDK CLI](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install)

In order to use the CDK CLI, you need to store your AWS IAM credentials in `~/.aws/credentials`. Use the credentials below:
```
[default]

```
Now create a Python virtual environment and install dependencies:
```
$ cd cdk
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install boto3
$ pip install aws_lambda_powertools
$ pip install cdklabs.generative_ai_cdk_constructs
```

Try running `cdk` in the terminal to make sure things are set up correctly. If you see a list of commands, you're good. Note that running any cdk commands on this draft stack will throw an error. This is expected.

## CDK changes

Take a look at `cdk/rivio_stack_homework/stack.py`. This CDK code sets up a Python lambda function, an API Gateway instance, and a Bedrock agent.

**Lambda**

Add the following environment variables to the lambda function:
- `IAM_ACCESS_KEY`: your AWS access key
- `IAM_SECRET_KEY`: your AWS secret key
- `NEO4J_URI`: "neo4j+s://672749ab.databases.neo4j.io"
- `NEO4J_USER`: "neo4j"
- `NEO4J_PASSWORD`: "BPnnI-xg52zfIkWN-w3J5MK5u1dDnu1bOLfuO9y6gp4"
- `AGENT_ID`: ""
- `AGENT_ALIAS_ID`: ""

(You will fill in `AGENT_ID` and `AGENT_ALIAS_ID` manually later)

**API Gateway**

Route the `/agent-smith` resource to the lambda function (hint: `aws_cdk` has a built-in class for this)

**Deployment**

- Deploy the stack (see _**Deploying CDK changes**_ in the Appendix section). Wait until the deployment succeeds to continue.
- Make sure Agent Smith is alive by logging into the AWS console and navigating to the following link: https://ca-central-1.console.aws.amazon.com/bedrock/home?region=ca-central-1#/agents. See _**Accessing the AWS console**_ in the Appendix section. Disregard the "Access denied" notifications.
- Create an agent alias through the Bedrock console
- You can now fill in the lambda's environment variables (`AGENT_ID` and `AGENT_ALIAS_ID`) with the values from the console (through the Lambda console). This unfortunately has to be done manually because [the Bedrock team screwed up the CDK construct recently](https://github.com/awslabs/generative-ai-cdk-constructs/issues/1044).
- Go to https://ca-central-1.console.aws.amazon.com/apigateway/ and deploy the API to the `homework` stage. Keep this tab open.

## Lambda changes

Now let's wire up the route we just created to our Bedrock agent. Open `lambda/lambda_function.py`.

- Complete the function `invoke_agent_smith()` to invoke the agent with a prompt (you'll find a helper function for this at the bottom of the file)
- Head back to the API Gateway service in the AWS console and grab the invoke URL of the `/agent-smith` endpoint (`Stages` tab)
- Use Postman or curl to send a request to this url, and Agent Smith should respond (see _**Chatting with Agent Smith**_ in the Appendix section)

# Part 2: Going from unstructured to structured data

This part involves running a notebook. If you're not familiar with Jupyter notebooks, don't worry, they're easy to use. Just make sure you are running the notebook in the correct environment by:
- Running `which python` in the terminal you've been using to deploy
- Opening the command palette in VS Code/Cursor (⌘ + ⇧ + P)
- Pasting the path in `Python: Select Interpreter` -> `Enter interpreter path`

You should now be able to run cells by clicking the 'Execute Cell' button.

The goal here is to extract structured data from an unstructured source (PDF file) and store it in a Neo4j graph database for the agent to access. To accomplish this, you'll first need to extract the content of the PDF file in plain text, then use an LLM to transform the content into JSON. Finally, you'll add the PO to the graph.

Open `notebook.ipynb` and:
- Complete `extract_text_from_pdf()` to extract the content of the example PDF in plain text (using PyPDF2)
- Complete `invoke_anthropic()`:
    - Fill in `PARTS_SCHEMA` so the LLM extracts the following fields: part_number, description, quantity, unit_price, total_price
    - Create system/user prompts, prompting the LLM to transform the PDF content into JSON that adheres to `PO_INFO_SCHEMA`
    - Call https://docs.anthropic.com/en/api/messages using the Anthropic SDK
- Complete the cypher query in `add_purchase_order()` (hint: LLMs are great at generating cyphers)

**IMPORTANT:** I added a playground at the bottom you can use to test your cyphers. At the very least, you should use it to make sure the purchase order was added successfully.
 
# Part 3: Making our agent a bit smarter

Now let's provide a new tool so Agent Smith can retrieve PO information. Note that you will now be editing the lambda function (`lambda_function.py`), which means you need to deploy your changes and call the agent to test them.

Powertools for AWS Lambda is being used here to reduce boilerplate code related to request parsing and routing. You'll want to check out this 17-min video explaining how the `BedrockAgentResolver` class works: https://www.youtube.com/watch?v=NWoC5FTSt7s. You can also skim through https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/bedrock_agents/.

We want to add a new function under `# AGENT ACTIONS #` that the agent can call to retrieve PO information from the graph given a supplier name. For this to work, you'll need to:
- Use the `@bedrock_agent_resolver.get` decorator so the function is included in the agent's schema (making sure to request the supplier name as a parameter)
- Use the `Neo4jService` class to query the graph as-follows:
```python
with Neo4jService._driver.session() as session:
    query = """
        ...
    """
    result = session.run(query, supplier_name=supplier_name)
    ...
```
- Find the correct cypher query (let's keep it simple and always retrieve all POs for a given supplier name)
- Regenerate the OpenAPI schema for the agent (see _**Generating the OpenAPI schema**_ in the Appendix section).
- Deploy the stack again
- Update the agent's alias version in the Bedrock console

To get Agent Smith to invoke this function, you can try asking the following: "_Do we have a PO with Dell Technologies?_"

🥁🥁🥁🥁🥁🥁🥁

If the agent returns the correct information, you're all set! If not, you'll want to check the logs in the AWS console (`CloudWatch` -> `Log groups` -> `agent-smith-lambda`) and go from there.

That's it! Please commit your code and let us know you're done. **No PR needed, just push your changes to the branch.**

# Appendix

## Deploying CDK changes

Open a terminal, navigate to the `cdk` directory, and run the following command:
```
$ cdk deploy
```

You can run ```cdk synth``` beforehand to check if everything compiles, and/or ```cdk diff``` to see the changes between your local stack and the one currently deployed.

**IMPORTANT:** Running `cdk deploy` will zip and deploy the lambda code automatically, but it will not bundle the dependencies. The following command must be run once after cloning the repo:
```
$ pip install -r ../lambda/requirements.txt -t ../lambda/lib
```

This will install the Python packages the lambda relies on in `/lib`, and automatically add them to the lambda archive going forward.

## Accessing the AWS console
- https://637423610292.signin.aws.amazon.com/console
- username: `homework`
- password: `AgentSmith@Rivio2025`

Make sure to switch to `ca-central-1` (Canada Central) after logging in (top-right corner dropdown).

## Chatting with Agent Smith

Just send a POST request to the API Gateway `/agent-smith` endpoint (once you've created it and wired it up) with the following body:
```json
{
    "prompt": "Hello"
}
```

You can follow the agent's trail of thoughts by looking at the lambda logs in the AWS console: `CloudWatch` -> `Log groups` -> `agent-smith-lambda`. Look for `invoke_agent(): trace =` log statements.

**IMPORTANT:** The agent will remember past conversations by default, which can quickly lead to bad answers when you're debugging your work. For example, if Agent Smith has already tried to call a tool and didn't receive the data it was hoping to get, it won't try to call this tool again during the same session. When this happens, send `exit` as a your prompt to the agent to clear the chat session.

## Generating the OpenAPI schema
Anytime you make a change to the agent's actions (add an action, edit a descripion, etc), you will need to re-generate the schema:
```bash
python ../lambda/lambda_function.py | python -m json.tool > ../lambda/openapi_schema.json
```

 **IMPORTANT:** AWS Bedrock is a newer service and can be unreliable at times. If the agent isn't responding as expected (cannot invoke the function you created, for instance), destroy the stack (`cdk destroy`) and re-deploy it.