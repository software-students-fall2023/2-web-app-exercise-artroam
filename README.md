# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

Artroam is a web application that empowers artists by providing a platform that serves as a vibrant, interactive canvas for creative expression. Here, we foster a global community of artists and art enthusiasts, where users can effortlessly showcase, discover, and connect with the world of art, whether it be through visual arts, digital art, photography and many more.

## User stories

[Issues Page](https://github.com/software-students-fall2023/2-web-app-exercise-artroam/issues)

1. As an artroam user, I want to be able to login into the app and sign up to create an account.
2. As an artroam user, I want to be able to see all the artworks available with their descriptions and authors.
3. As an artroam user, I want to be able to set my profile picture on my profile page. 
4. As an artroam user, I want to be able to login into the app and have / maintain a profile.
5. As an artoroam user, I want to be able to capture or upload a photo and post it with a comment.

## Task boards

[Taskboard Sprint 1](https://github.com/orgs/software-students-fall2023/projects/3)


[Taskboard Sprint 2](https://github.com/orgs/software-students-fall2023/projects/31)

## Webapp Setup
Firstly you must create a `.env` file within the directory of the cloned repository. Within this file you must include the following based on the values provided: 
```
MONGO_DBNAME
MONGO_URI
FLASK_APP
FLASK_ENV
GITHUB_SECRET
GITHUB_REPO
APP_SECRET_KEY
AWS_SECRET_ACCESS_KEY
AWS_ACCESS_KEY_ID
BUCKET_NAME
```

1. Go to [AWS website](https://aws.amazon.com/cli/) and download AWS Command Line Interface based on your operating system.
2. Go to terminal and type the following line:
`aws configure`
3. Follow the prompt and provide values: 
```
AWS Access Key ID: <Value for variable AWS_ACCESS_KEY_ID in provided .env file>
AWS Secret Access Key: <Value for variable AWS_SECRET_ACCESS_KEY in provided .env file>
Default region name: us-east-1
Default output format: json
```
4. Type the following line after setting up AWS:
`pip install -r requirements.txt`
5. Create and Activate virtual environment:
`python3 -m venv .venv`
`source .venv/bin/activate`
6. Run the app:
`flask run`
