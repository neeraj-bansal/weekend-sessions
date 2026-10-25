# Set up a free AWS account, the AWS CLI, Amazon Bedrock and Strands Agents

A step-by-step student guide for macOS and VS Code.

By the end of this guide you will have a working AWS account on the Free plan, the AWS CLI connected to it from the VS Code terminal, permission to use Amazon Bedrock, and the Strands Agents library installed so a Python agent can call a Claude model on Bedrock from your own machine.

| Part | What you do | You are done when |
|---|---|---|
| 1 | Create a free AWS account | The console shows your Free plan banner and credits |
| 2 | Create an IAM user and access key for the CLI | The user has the `AmazonBedrockFullAccess` policy |
| 3 | Install and configure the AWS CLI in VS Code | `aws sts get-caller-identity` shows your IAM user |
| 4 | Check Bedrock from the CLI | A model replies to a test message |
| 5 | Install Strands Agents and run a test agent | The agent prints a reply from Bedrock |

**Before you start.** You need a Mac with VS Code and Python 3 installed, an email address, a phone that can receive a verification code, and a debit or credit card. Allow about 45 minutes. New accounts can be blocked from using Bedrock for up to two hours while AWS verifies them (see Part 4), so create your account first and do something else while you wait.

---

## Part 1. Create a free AWS account

### What the Free plan gives you

AWS replaced the old 12-month free tier for accounts created after 15 July 2025. A new account on the Free plan gets **$100 in credits** straight away and can earn up to $100 more by completing onboarding activities in the console (one of them is trying Amazon Bedrock). The plan ends after 6 months or when the credits run out, whichever comes first, and a Free plan account is not charged beyond its credits. A card is still required at sign-up to verify your identity. Credits are for genuinely new customers, so do not create a second account or join an existing AWS Organization.

### Steps

1. Go to [aws.amazon.com/free](https://aws.amazon.com/free) and choose **Create free account**.
2. Enter your email address and an account name, then enter the verification code AWS emails you.
3. Set a strong root password and choose **Personal** as the account type.
4. Fill in your contact details, then add your payment card.
5. Verify your phone number with the code AWS sends by text or call. Never share this code with anyone.
6. When asked to pick a plan, choose the **Free plan**, not the Paid plan.
7. Sign in to the AWS Management Console as the root user with the email and password you just set.

### Check it worked

In the console search bar open **Billing and Cost Management**, then **Free Tier**. You should see a banner saying *Your free plan account does not get charged* and a credit balance of about $100. The introduction text on that page may still mention 12 months. That text is out of date, so go by the banner and the credits.

Also set your console region (top right) to **US West (Oregon) `us-west-2`**. We use that region for Bedrock throughout this guide.

---

## Part 2. Create an IAM user and access key for the CLI

The root user can do everything in your account, so you should never put its keys on your laptop. Instead you create a limited IAM user that can only use Bedrock, and give the CLI that user's key.

1. In the console search bar open **IAM**, then **Users**, then **Create user**.
2. Name the user `bedrock-cli-user`. Leave *Provide user access to the AWS Management Console* unticked, since this user is only for the CLI.
3. Choose **Attach policies directly**, tick `AmazonBedrockFullAccess`, and create the user.
4. Open the new user, go to the **Security credentials** tab and choose **Create access key**.
5. Pick **Command Line Interface (CLI)** as the use case, tick the confirmation box and continue. AWS may suggest alternatives such as IAM Identity Center. For a personal learning account you can continue with an access key.
6. On the last screen copy the **Access key ID** and the **Secret access key** (use *Show*) into a safe place, or choose **Download .csv file**, then choose **Done**.

> *(Screenshot omitted: the last screen of the access key wizard. The secret key is hidden until you click Show, and AWS will not show it again after you leave.)*

> **Protect your keys.** The secret access key is shown only once. Never paste it into a chat, a screenshot, a script or a Git repository. If it ever leaks, open IAM, then the user, then Security credentials, make the key inactive, delete it and create a new one.

---

## Part 3. Install the AWS CLI and connect it to VS Code

Open a terminal inside VS Code: **Terminal** menu, then **New Terminal** (or press Ctrl + `` ` ``). The VS Code terminal uses the same shell and the same `~/.aws` settings as your normal Mac terminal, so once the CLI is configured here it works everywhere. Opening a project folder first (File, Open Folder) keeps your files for this course in one place.

### Step 1. Install the CLI

The easiest way is Homebrew:

```bash
brew install awscli
```

If you do not use Homebrew, use the official installer instead:

```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

Check the install:

```bash
aws --version
```

### Step 2. Give the CLI your key

```bash
aws configure
```

| Prompt | What to enter |
|---|---|
| AWS Access Key ID | The access key ID from Part 2 |
| AWS Secret Access Key | The secret access key from Part 2 (it will not be shown as you paste it) |
| Default region name | `us-west-2` |
| Default output format | `json` |

### Step 3. Check the connection

```bash
aws sts get-caller-identity
```

You should get three lines back, and the `Arn` must end in `user/bedrock-cli-user`:

```json
{
    "UserId": "AIDA................",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/bedrock-cli-user"
}
```

> **If a screen full of text appears and the terminal seems stuck.** Some AWS CLI output opens in a scrolling viewer (a pager). If you see `(END)` or a HELP page, press `q` to leave it. To stop it happening again, run `aws configure set cli_pager ""` once. For the current terminal window only, you can run `export AWS_PAGER=""`.

---

## Part 4. Check that Bedrock works from the CLI

Your IAM user already has the Bedrock permission from Part 2. Recent Claude models on Bedrock are called through *inference profile IDs* that start with a geography such as `us.` or `global.`. First list the Claude profiles your account can see in `us-west-2`:

```bash
aws bedrock list-inference-profiles --region us-west-2 \
  --query "inferenceProfileSummaries[?contains(inferenceProfileId,'claude')].inferenceProfileId" \
  --output table
```

Choose one ID from your own table. Model lists change over time, so always copy from your own output. In this guide we use a small, low-cost model, `us.anthropic.claude-haiku-5-5`, to save your credits. Now send it a test message:

```bash
aws bedrock-runtime converse --region us-west-2 \
  --model-id us.anthropic.claude-haiku-5-5 \
  --messages '[{"role":"user","content":[{"text":"Say hello in one short line"}]}]'
```

**What success looks like:** a block of JSON that contains the model's greeting under `"text"` and `"stopReason": "end_turn"`. That confirms your account, key, permissions and region all work together.

### The most common first-day error

> *(Screenshot omitted: the model list, followed by the verification message that new accounts can see on their first call.)*

If you see `AccessDeniedException ... Your account is currently being verified`, nothing is wrong with your setup. AWS holds back model calls on brand-new accounts until its checks finish.

- **Wait.** Verification normally takes less than 2 hours, then run the same command again.
- Check your inbox and spam folder for any email from AWS asking for more information, and complete it.
- If you still get the message after more than 2 hours, email `aws-verification@amazon.com` with your account ID and a copy of the error.

---

## Part 5. Install Strands Agents and run a test agent

Strands Agents is an open-source Python library for building AI agents. It uses Amazon Bedrock as its default model provider, and it finds your AWS credentials from the same `aws configure` settings you just created. Install it in a virtual environment so it stays separate from other Python projects.

### Step 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt should now start with `(.venv)`. Each time you open a new terminal for this work, run the `source` line again.

### Step 2. Install the libraries

```bash
pip install strands-agents strands-agents-tools boto3
python -c "import strands; print('strands ok')"
```

It should print `strands ok`.

### Step 3. Create and run the test agent

Strands defaults to a Claude Sonnet model in `us-west-2`. To stay on the low-cost model we already tested, the script below names the model and region explicitly. In VS Code create a file called `test_strands.py` with this content (or paste the block into the terminal):

```bash
cat > test_strands.py << 'EOF'
from strands import Agent
from strands.models import BedrockModel
model = BedrockModel(model_id="us.anthropic.claude-haiku-5-5", region_name="us-west-2")
agent = Agent(model=model)
print(agent("Say hello in one short line"))
EOF
python test_strands.py
```

**What success looks like:** the agent prints a short greeting from the model. If you get a verification or access error, go back to Part 4, because Strands uses exactly the same Bedrock access as the CLI test.

---

## Troubleshooting

| What you see | What it means and what to do |
|---|---|
| Terminal shows `(END)` or a HELP page and will not accept commands | The AWS CLI opened its pager. Press `q`. Turn it off with `aws configure set cli_pager ""`. |
| `AccessDeniedException ... account is currently being verified` | New-account check. Wait up to 2 hours and retry. After 2 hours, email `aws-verification@amazon.com`. |
| `Unable to locate credentials` | The CLI has no key yet. Run `aws configure`, then `aws configure list` to see what it found. |
| `InvalidClientTokenId` or `SignatureDoesNotMatch` | The key was mistyped or partly copied. Re-run `aws configure`. If the secret is lost, create a new key in IAM and delete the old one. |
| `AccessDenied` that is not the verification message | Open IAM, then Users, then `bedrock-cli-user`, then Permissions, and confirm `AmazonBedrockFullAccess` is attached directly. |
| `ValidationException`, invalid model ID, or model not available | Copy the ID exactly from your own `list-inference-profiles` table, and keep `--region us-west-2` on every command. If the console asks you to accept a one-time model use-case form, complete it in the Bedrock console and retry. |
| `aws: command not found` | Close and reopen the terminal. If it persists, reinstall using the other method in Part 3. |
| pip says `externally-managed-environment` | You are outside a virtual environment. Run `source .venv/bin/activate` and install again. |
| `(.venv)` is missing from the prompt | Run `source .venv/bin/activate` from the folder that contains `.venv`. |

## Keep your credits and account safe

- Stay on the Free plan. Upgrading to the Paid plan means charges start once your credits are used.
- The account closes automatically after 6 months or when the credits are used up, so do not store anything you need to keep long term.
- Never share your access key, secret key or phone codes, and never include them in screenshots.
- When the course ends, delete the access key (IAM, then the user, then Security credentials) so it cannot be misused.

## Quick checklist

| Done | Check | Command or place |
|---|---|---|
| [ ] | Free plan banner and credits visible | Console, Billing and Cost Management, Free Tier |
| [ ] | IAM user with Bedrock policy | IAM, Users, `bedrock-cli-user` |
| [ ] | CLI sees your user | `aws sts get-caller-identity` |
| [ ] | A model answers from the CLI | `aws bedrock-runtime converse ...` |
| [ ] | Strands agent answers | `python test_strands.py` |

## Sources

- AWS Billing documentation: [Explore services with AWS Free Tier](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html)
- AWS Bedrock documentation: [Request access to models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- [Strands Agents Python quickstart](https://strandsagents.com/docs/user-guide/sdk/quickstart/python/)
- AWS Builder Center: *The AWS Free Tier changed in 2026* (builder.aws.com)

Free plan figures were checked against AWS and independent write-ups in October 2026; AWS can change them, so re-check [aws.amazon.com/free](https://aws.amazon.com/free) before you sign up.
