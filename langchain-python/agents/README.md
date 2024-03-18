# Multi-agent demo

## Goal

This folder is a demo of the capabilities of Gemini in a multi-agents setting (~ AutoGen implementation).

In this demo, we have two agents with the following roles and tools:

- **Agent coordinator**: This agent is in charge of coordinating the execution of the other agents. It is directly interacting with end-users and has all the knowledge about the culture of a fictional company. It has the following tool:
  - **Knowledge base**: This tool enables the coordinator agent to communicate with the second agent of this demo, *agent knowledge base*.
- **Agent knowledge base**: This agent is in charge of retrieving information from its foundational knowledge. It has the following tools:
  - **Rewrite answer**: This tool enables the knowledge base agent to rewrite its answer, before giving an actual answer to the coordinator agent. It will be used to add some personality to the agent. This tool is implemented by forcing the agent to collaborate with the *agent coordinator*. In a real-world scenario, we would probably have used a third agent, responsible for culture/personality, but we wanted to demonstrate two-ways communication between agents.

Here is a normal interaction between the end-users and the agents:

1. The end-user asks a question to the *agent coordinator*: *e.g. What is Google Cloud?*.
2. The *agent coordinator* asks the *knowledge base agent*: *e.g. What is Google Cloud?*.
3. The *knowledge base agent* forms a preliminary answer: *e.g. Google Cloud is a suite of cloud computing services*.
4. Before sending its answer back, the *knowledge base agent* asks the *agent coordinator* to rewrite the answer: *e.g. Can you add some personality to the answer: Google Cloud is a suite of cloud computing services?*.
5. The *agent coordinator* rewrites the answer: *e.g. Google Cloud is a suite of cloud computing services, which is awesome!*
6. The *knowledge base agent* sends the answer back to the *agent coordinator*.
7. The *agent coordinator* may potentially ask follow up questions to the *knowledge base agent*, further refining its answer: *e.g. What are the different services of Google Cloud?*. In this case, go back to step 3.
8. Otherwise, the *agent coordinator* sends the answer back to the end-user.

The demo currently runs on Google Cloud Platform, using the following services:

- **Cloud Run**: This service is used to deploy the agents. It is a serverless service, which means that the agents are only running when they are invoked. This service is used to deploy the *agent coordinator* and the *agent knowledge base*.
- **Cloud Build**: This service is used to build the agents and deploy them on Cloud Run.
- **Cloud Datastore**: This service is used to store the history of the conversations between the agents and the end-users.
- **Vertex AI**: This service is used to communicate with Gemini Pro.

While the demo can be directly accessed using the application in the `test-invoke` folder, it is also possible to interact with the agents locally, making it easier to see the interactions between the different agents.

The agents are deployed on Google Cloud Platform at every commit. So every time you commit a new change, it will be reflected in the agents, deployed on Cloud Run, after the corresponding Cloud Build triggers have been executed.

## Structure

This folder is structured as follows:

  - `agent-coordinator/`: This folder contains the application of the agent coordinator.
  - `agent-knowledge-base/`: This folder contains the application of the agent knowledge base.
  - `test-invoke/`: This folder contains a simple application to test the invocation of the agents through Cloud Run.

## How to run the demo locally

### Prerequisites

- Python 3.10
- Google Cloud CLI (`gcloud`) installed and configured to use a project with Vertex AI enabled (for Gemini Pro)
  - To configure the CLI, run `gcloud init` and follow the instructions.
  - To enable Vertex AI, run `gcloud services enable vertexai.googleapis.com`.
  - To set the project, run `gcloud config set project <project-id>`.
- Install the dependencies of the coordinator (`apps/agent-coordinator/requirements.txt`) and knowledge base (`apps/agent-knowledge-base/requirements.txt`) agents: `pip install -r requirements.txt`

### Run the demo

1. Run the coordinator agent: `python apps/agent-coordinator/main.py`
2. Run the knowledge base agent: `python apps/agent-knowledge-base/main.py`
3. Run the following command:

``` bash
curl --location --request POST 'http://localhost:8080/invoke' \
    --header 'Content-Type: application/json' \
    --header "Authorization: Bearer fake-local-token" \
    --data-raw '{
        "input": {
            "message": "What is Google Cloud?",
            "session_id": "1234567890"
        }
    }'
```

or adapt it to your needs. Please note that the `session_id` variable is used to identify the conversation between the end-user and the agents. If you want to start a new conversation, you need to change the `session_id` variable. The authorization bearer does not matter in this case, as we are running the demo locally.

To see the agents in action, you can look at the logs of the coordinator and knowledge base agents. It will give you a better understanding of the interactions between the agents, as well as the internal thought process of the different agents.
