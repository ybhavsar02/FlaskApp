pipeline {
    agent any

    // ─── Environment Variables ───────────────────────────────────────────────
    environment {
        APP_NAME        = 'flask-devops-app'
        AWS_REGION      = 'ap-south-1'
        AWS_ACCOUNT_ID  = credentials('aws-account-id')
        ECR_REPO        = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"
        IMAGE_TAG       = "${BUILD_NUMBER}"
        GIT_REPO        = 'https://github.com/your-username/flask-devops-project.git'
    }

    // ─── Build Options ───────────────────────────────────────────────────────
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    // ─── Trigger on GitHub push ──────────────────────────────────────────────
    triggers {
        githubPush()
    }

    // ─── Stages ──────────────────────────────────────────────────────────────
    stages {

        stage('Checkout') {
            steps {
                echo "=== Checking out source code ==="
                git branch: 'main', url: "${GIT_REPO}"
                script {
                    env.GIT_COMMIT_MSG = sh(
                        script: 'git log -1 --pretty=%B',
                        returnStdout: true
                    ).trim()
                    echo "Commit: ${env.GIT_COMMIT_MSG}"
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                echo "=== Installing Python dependencies ==="
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Unit Tests') {
            steps {
                echo "=== Running Unit Tests ==="
                sh '''
                    . venv/bin/activate
                    pytest tests/ -v --cov=app --cov-report=xml --cov-report=term-missing
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: '**/test-results.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }

        stage('Code Quality Check') {
            steps {
                echo "=== Running static code analysis ==="
                sh '''
                    . venv/bin/activate
                    pip install flake8
                    flake8 app.py --max-line-length=120 --ignore=E501 || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "=== Building Docker image ==="
                sh '''
                    docker build \
                        --build-arg APP_VERSION=${IMAGE_TAG} \
                        -t ${APP_NAME}:${IMAGE_TAG} \
                        -t ${APP_NAME}:latest \
                        .
                '''
            }
        }

        stage('Push to AWS ECR') {
            steps {
                echo "=== Pushing image to ECR ==="
                withAWS(region: "${AWS_REGION}", credentials: 'aws-credentials') {
                    sh '''
                        # Authenticate to ECR
                        aws ecr get-login-password --region ${AWS_REGION} | \
                            docker login --username AWS --password-stdin ${ECR_REPO}

                        # Create ECR repo if not exists
                        aws ecr describe-repositories --repository-names ${APP_NAME} \
                            --region ${AWS_REGION} || \
                            aws ecr create-repository --repository-name ${APP_NAME} \
                            --region ${AWS_REGION}

                        # Tag and push
                        docker tag ${APP_NAME}:${IMAGE_TAG} ${ECR_REPO}:${IMAGE_TAG}
                        docker tag ${APP_NAME}:latest ${ECR_REPO}:latest
                        docker push ${ECR_REPO}:${IMAGE_TAG}
                        docker push ${ECR_REPO}:latest
                    '''
                }
            }
        }

        stage('Deploy to DEV') {
            when {
                branch 'develop'
            }
            steps {
                echo "=== Deploying to DEV environment ==="
                sh """
                    ansible-playbook -i ansible/inventory/dev ansible/deploy.yml \
                        -e "image_tag=${IMAGE_TAG}" \
                        -e "ecr_repo=${ECR_REPO}" \
                        -e "app_env=dev"
                """
            }
        }

        stage('Deploy to QA') {
            when {
                branch 'release'
            }
            steps {
                echo "=== Deploying to QA environment ==="
                sh """
                    ansible-playbook -i ansible/inventory/qa ansible/deploy.yml \
                        -e "image_tag=${IMAGE_TAG}" \
                        -e "ecr_repo=${ECR_REPO}" \
                        -e "app_env=qa"
                """
            }
        }

        stage('Approval for Production') {
            when {
                branch 'main'
            }
            steps {
                timeout(time: 15, unit: 'MINUTES') {
                    input message: "Approve deployment to PRODUCTION?",
                          ok: "Deploy",
                          submitter: "devops-lead,manager"
                }
            }
        }

        stage('Deploy to PROD') {
            when {
                branch 'main'
            }
            steps {
                echo "=== Deploying to PRODUCTION ==="
                sh """
                    ansible-playbook -i ansible/inventory/prod ansible/deploy.yml \
                        -e "image_tag=${IMAGE_TAG}" \
                        -e "ecr_repo=${ECR_REPO}" \
                        -e "app_env=prod"
                """
            }
        }

        stage('Health Check') {
            steps {
                echo "=== Running post-deployment health check ==="
                script {
                    def retries = 5
                    def success = false
                    for (int i = 0; i < retries; i++) {
                        try {
                            def response = sh(
                                script: "curl -s -o /dev/null -w '%{http_code}' http://your-ec2-ip/health",
                                returnStdout: true
                            ).trim()
                            if (response == '200') {
                                echo "Health check passed!"
                                success = true
                                break
                            }
                        } catch (err) {
                            echo "Attempt ${i+1} failed. Retrying in 10s..."
                            sleep(10)
                        }
                    }
                    if (!success) {
                        error "Health check failed after ${retries} attempts. Triggering rollback."
                    }
                }
            }
        }
    }

    // ─── Post Actions ─────────────────────────────────────────────────────────
    post {
        success {
            echo "=== Pipeline SUCCEEDED ==="
            echo "Image ${ECR_REPO}:${IMAGE_TAG} deployed successfully."
        }
        failure {
            echo "=== Pipeline FAILED. Initiating rollback ==="
            sh """
                ansible-playbook -i ansible/inventory/prod ansible/rollback.yml \
                    -e "ecr_repo=${ECR_REPO}" || true
            """
        }
        always {
            echo "=== Cleaning up Docker images ==="
            sh 'docker rmi ${APP_NAME}:${IMAGE_TAG} || true'
            cleanWs()
        }
    }
}
