import aws_cdk as cdk

from rivio_stack_homework.stack import HomeworkStack

app = cdk.App()

HomeworkStack(
    app,
    "rivio-stack-homework",
    env = cdk.Environment(account='637423610292', region='ca-central-1'),
    )

app.synth()