from strands import Agent
from strands.models import BedrockModel

# claude-haiku-5-5 is listed but not available to this account, so use Haiku 4.5.
model = BedrockModel(
    model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0", region_name="us-west-2"
)
agent = Agent(model=model)
print(agent("Say hello in one short line"))
