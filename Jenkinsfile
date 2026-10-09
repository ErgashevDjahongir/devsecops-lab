
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
        IMAGE_NAME      = 'devsecops-demo'
        DEPENDENCY_DATA = '/opt/devsecops/dependency-data-clean'
        TRIVY_CACHE     = '/opt/devsecops/trivy-cache'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm

                sh '''
                    set -eu
                    mkdir -p "$WORKSPACE/reports"
                '''
            }
        }

        stage('SAST - Semgrep') {
            steps {
                sh '''
                    set -eu

                    docker run --rm \
                      -v "$WORKSPACE:/src" \
                      semgrep/semgrep:latest \
                      semgrep scan \
                      --config auto \
                      /src \
                      --json \
                      --output /src/reports/semgrep.json
                '''
            }
        }

        stage('Secrets - Gitleaks') {
            steps {
                sh '''
                    set -eu

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
                    set -eu

                    mkdir -p "$WORKSPACE/reports"

                    test -d "$DEPENDENCY_DATA" || {
                        echo "ERROR: Dependency-Check data papkasi topilmadi"
                        exit 1
                    }

                    docker run --rm \
                      --user "$(id -u):$(id -g)" \
                      -v "$WORKSPACE:/src" \
                      -v "$DEPENDENCY_DATA:/usr/share/dependency-check/data" \
                      owasp/dependency-check:latest \
                      --scan /src \
                      --format JSON \
                      --out /src/reports \
                      --noupdate

                    test -s "$WORKSPACE/reports/dependency-check-report.json"

                    python3 -m json.tool \
                      "$WORKSPACE/reports/dependency-check-report.json" \
                      > /dev/null

                    echo "Dependency-Check JSON hisoboti muvaffaqiyatli yaratildi."
                '''
            }
        }

        stage('Build container') {
            steps {
                sh '''
                    set -eu

                    docker build \
                      -t "$IMAGE_NAME:$BUILD_NUMBER" .
                '''
            }
        }

        stage('Container - Trivy') {
            steps {
                sh '''
                    set -eu

                    mkdir -p "$TRIVY_CACHE" "$WORKSPACE/reports"

                    docker run --rm \
                      -v /var/run/docker.sock:/var/run/docker.sock \
                      -v "$TRIVY_CACHE:/root/.cache/" \
                      -v "$WORKSPACE/reports:/reports" \
                      aquasec/trivy:latest \
                      image \
                      --format json \
                      --output /reports/trivy-image.json \
                      "$IMAGE_NAME:$BUILD_NUMBER"

                    test -s "$WORKSPACE/reports/trivy-image.json"

                    echo "Trivy JSON hisoboti yaratildi."
                '''
            }
        }

        stage('DAST - OWASP ZAP') {
            steps {
                sh '''
                    set -eu

                    NET="devsecops-${BUILD_NUMBER}"
                    APP="devsecops-app-${BUILD_NUMBER}"
                    ZAP_WORK="$WORKSPACE/.zap-work-${BUILD_NUMBER}"

                    cleanup() {
                        docker rm -f "$APP" >/dev/null 2>&1 || true
                        docker network rm "$NET" >/dev/null 2>&1 || true
                        rm -rf "$ZAP_WORK"
                    }

                    # Shu build uchun avvalgi qoldiqlarni tozalash
                    cleanup

                    mkdir -p "$WORKSPACE/reports" "$ZAP_WORK"

                    # Faqat vaqtinchalik ZAP ish papkasiga yozish huquqi
                    chmod 777 "$ZAP_WORK"

                    trap cleanup EXIT

                    docker network create "$NET"

                    docker run -d \
                      --name "$APP" \
                      --network "$NET" \
                      "$IMAGE_NAME:$BUILD_NUMBER"

                    echo "OWASP ZAP skanerlash boshlandi..."

                    docker run --rm \
                      --network "$NET" \
                      -v "$ZAP_WORK:/zap/wrk/:rw" \
                      ghcr.io/zaproxy/zaproxy:stable \
                      zap-baseline.py \
                      -t "http://$APP:5000" \
                      -J zap-report.json

                    # Hisobot yaratilganini va bo'sh emasligini tekshirish
                    test -s "$ZAP_WORK/zap-report.json"

                    # Hisobotni Jenkins workspace ichiga ko'chirish
                    cp "$ZAP_WORK/zap-report.json" \
                       "$WORKSPACE/reports/zap-report.json"

                    test -s "$WORKSPACE/reports/zap-report.json"

                    echo "OWASP ZAP JSON hisoboti muvaffaqiyatli yaratildi."
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
