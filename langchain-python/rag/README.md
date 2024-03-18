# How to deploy a Cloud Run service
This folder contains a sample Cloud Run service to interact with an LLM.

To deploy this code to Cloud Run, use the following command:

```
gcloud run deploy [SERVICE_NAME] --memory 2Gi --region [REGION] --source .
```

If prompted to create an Artifact Registry repository to store artifacts, select yes.

You will be prompted to choose whether you want to allow unauthenticated requests. If you select yes, no authentication will be required to send requests to your service. If you select no, only authenticated requests from users having the Cloud Run Invoker role on the service will be fulfilled. We recommend making authentication required.

Once the build is finished, you can send a sample request by running:

```
curl \
-X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $(gcloud auth print-identity-token)" \
[CLOUD_RUN_URL] -d '{
"question": "What is the first rule of Machine Learning?"}'
```

To get the correct URL, go to the GCP console and search "Cloud Run". Click on the service you have just created, then copy the URL next to the service name on the top.

Further links:

* Deploying to Cloud Run: https://cloud.google.com/run/docs/deploying-source-code

* Setting up the gcloud command: https://cloud.google.com/sdk/docs/initializing 