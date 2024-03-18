# dgc-langchain-samples
Sample code for Langchain

## Langchain JS
The **langchain-next-js** folder contains an example of Langchain JS app. This app includes 3 use cases: chat, RAG and function calling.
To deploy on Cloud Run, follow these steps:

* Install the [gcloud CLI](https://cloud.google.com/sdk/docs/install) and [Docker](https://docs.docker.com/engine/install/).
* Configure Docker authentication to Artifact Registry
```
gcloud auth configure-docker REGION-docker.pkg.dev
```
* Build and push your app
```
docker build -t REGION-docker.pkg.dev/PROJECT/containers/langchain-next-js:latest ./langchain-next-js
docker push REGION-docker.pkg.dev/PROJECT/containers/langchain-next-js:latest
```
* Replace REGION and PROJECT with your own values in *service.yaml*
* Deploy on Cloud Run
```
gcloud run services replace --project=PROJECT --region=REGION service.yaml
```

## Langchain Python
The **langchain-python** folder contains examples of Langchain Python apps. 
* The **agents** folder contains a Gemini demo in a multi-agent setting, for more information on how to run it refer to the [README](./langchain-python/agents/README.md).
* The **notebooks** folder contains 3 Jupyter notebooks with text summarization examples and Q&A chatbots (both from local datastores and from web pages). 
* The **rag** folder contains an example of RAG on Cloud Run. For more information on how to deploy, refer to the [README](./langchain-python/rag/README.md).
