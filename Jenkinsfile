pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    environment {
        IMAGE_NAME = 'devsecops-demo'
	DEPENDENCY_DATA = '/opt/devsecops/dependency-data-clean'
        TRIVY_CACHE = '/opt/devsecops/trivy-cache'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'mkdir -p reports'
            }
        }

        stage('SAST - Semgrep') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$WORKSPACE:/src" \
                      semgrep/semgrep:latest \
                      semgrep scan --config auto /src \
                      --json --output /src/reports/semgrep.json
                '''
            }
        }

        stage('Secrets - Gitleaks') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$WORKSPACE:/src" \
                      ghcr.io/gitleaks/gitleaks:latest \
                      dir /src \
                      --report-format json \
                      --report-path /src/reports/gitleaks.json \
                      --exit-code 0
                '''
            }
        }

        stage('SCA - Dependency-Check') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$WORKSPACE:/src" \
                      -v "$DEPENDENCY_DATA:/usr/share/dependency-check/data" \
                      owasp/dependency-check:latest \
                      --scan /src \
                      --format JSON \
                      --out /src/reports/dependency-check.json \
                      --noupdate
                '''
            }
        }

        stage('Build container') {
            steps {
                sh '''
                    docker build \
                      -t "$IMAGE_NAME:$BUILD_NUMBER" .
                '''
            }
        }

        stage('Container - Trivy') {
            steps {
                sh '''
                    docker run --rm \
                      -v /var/run/docker.sock:/var/run/docker.sock \
                      -v "$TRIVY_CACHE:/root/.cache/" \
                      -v "$WORKSPACE/reports:/reports" \
                      aquasec/trivy:latest \
                      image --format json \
                      --output /reports/trivy-image.json \
                      "$IMAGE_NAME:$BUILD_NUMBER"
                '''
            }
        }

        stage('DAST - OWASP ZAP') {
            steps {
                sh '''
                    set -eu

                    NET="devsecops-${BUILD_NUMBER}"
                    APP="devsecops-app-${BUILD_NUMBER}"

                    cleanup() {
                      docker rm -f "$APP" >/dev/null 2>&1 || true
                      docker network rm "$NET" >/dev/null 2>&1 || true
                    }

                    cleanup
                    docker network create "$NET"

                    trap cleanup EXIT

                    docker run -d \
                      --name "$APP" \
                      --network "$NET" \
                      "$IMAGE_NAME:$BUILD_NUMBER"

                    docker run --rm \
                      --network "$NET" \
                      -v "$WORKSPACE/reports:/zap/wrk/:rw" \
                      ghcr.io/zaproxy/zaproxy:stable \
                      zap-baseline.py \
                      -t "http://$APP:5000" \
                      -J zap-report.json
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'reports/**/*,reports/*',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }

        cleanup {
            sh '''
                docker image rm \
                  "$IMAGE_NAME:$BUILD_NUMBER" \
                  >/dev/null 2>&1 || true
            '''
        }
    }
}
