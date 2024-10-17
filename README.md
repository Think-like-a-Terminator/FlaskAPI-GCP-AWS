🚀 Python Flask CRUD API | GCP App Engine | Google Datastore & Buckets | AWS SES Email Notifications

This project is built to provide a fully functional CRUD (Create, Read, Update, Delete) API, deployed on Google Cloud Platform (GCP) App Engine, utilizing Google Cloud Datastore as a NoSQL backend, using GCP Buckets to store files and generating signed URLs for downloading files, and also leveraging AWS SES for sending email notifications. You can have a production scale API and backend for your frontend or any application.

<br/>

📊 Key Features:

Fully Functional CRUD API: Create, read, update, and delete data using Google Datastore as the backend (Highly Scalable NoSQL Backend: Using Google Cloud Datastore ensures flexibility and performance even as data grows).

Scalable Deployment: Deployed on GCP App Engine, optimized with cost-saving automatic scaling settings (automatic_scaling and max_instances set to 1, can increase if needed. If API is not in use, reduces cost by having min_instances set to 0, otherwise set to 1 to have it always on/ready).

Store and Download Files via API: Create buckets, store files, and download files from GCP buckets

Email Notifications: Integrates with AWS SES to send transactional and marketing emails.

<br/>

Why GCP App Engine?

Instance Class (F4_1G): This is a high performance automatic scaling instance type, ensuring your app can handle substantial load while running efficiently, however you can change it to less powerful instances, view instance classes here:  https://cloud.google.com/appengine/docs/standard/

Automatic Scaling: Set to limit max_instances to 1 for cost control, but you can increase this to handle larger traffic volumes easily.

<br/>

🔧 Google Cloud Datastore: The Ideal NoSQL Backend

This project uses Google Cloud Datastore as its backend, providing a flexible and scalable NoSQL database solution. Here’s why Datastore is perfect for your project:

Schema-Free: Datastore is schema-less, meaning it can adapt as your data model evolves, which is ideal for a CRUD API.

High Scalability: Whether you're handling a few dozen or millions of records, Datastore scales automatically, with high availability and low-latency responses.

Integrates Seamlessly: Datastore works effortlessly with Google Cloud services and is a reliable choice for both backend systems and front-end applications.

Datastore Advantages:

Easy integration with Python Flask.

Efficient indexing for queries, meaning faster lookups.

Scalable architecture without the need for complex database management.

<br/>

💌 AWS SES (Simple Email Service): Email Notifications Made Simple

For sending emails, this API integrates with AWS SES (Simple Email Service), one of the best email solutions for developers. AWS SES is designed for sending marketing emails, transactional emails, and system notifications.

Why AWS SES?

Cost-Effective: SES offers one of the most affordable and reliable email services available, ideal for projects that need to send large volumes of emails.

High Deliverability: AWS SES is trusted for its deliverability, ensuring your emails avoid spam filters and land in the inbox.

Seamless Integration: The integration with Flask allows the system to send out critical notifications, confirmations, and marketing emails at the right time with minimal configuration.

<br/>

🌟 What's Inside This Repository?

A Python main.py file that performs full API CRUD operations, stores and downloads files from GCP bucket, and sends emails via AWS SES.

A app.yaml configuration file for GCP App Engine deployment.

A awsses.py file to have AWS SES integrated into the API to send email notifications (e.g., marketing, system alerts, user confirmations).

<br/>

🚀 Getting Started

Set up GCP Cloud SDK or use GCP Cloud Shell inside your browser (easy way).

Clone the repository:

git clone the repository inside a folder in GCP Cloud Shell or your local machine.

Add in your parameters:

Configure your app.yaml parameters to suit your needs, this file specifies the configuration for deploying to App Engine. This file includes settings like instance_class and automatic_scaling.

Add in the path to your GCP Service Account Credentials JSON file and AWS SES credentials file inside main.py.

(Optional) If you want to leverage creating GCP buckets from your frontend, enter your frontend URL inside cors_configuration under the class CreateGcpBucket(Resource), replace "INSERT YOUR FRONTEND URL" with your frontend URL.

Run the command in Cloud Shell where the app.yaml and .py files are located in:

gcloud app deploy

Select location.

Access the Deployed API: Once deployed, you can copy and paste your App Engine URL to interact with the API, this main.py file adds an extension to the URL i.e. /api/v1/.. (add this to the end of the App Engine URL)

<br/>

🔮 Important Notes:

This API has basic Auth, consider adding OAuth Integration: Adding secure authentication with OAuth for user access.  Or, you can specify in app engine for your API to only listen to traffic from specific ports or from a frontend or app also on GCP app engine.


