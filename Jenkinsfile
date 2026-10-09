
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

                    test -s "$WORKSPACE/reports/semgrep.json"
                    echo "Semgrep hisoboti yaratildi."
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

                    test -s "$WORKSPACE/reports/gitleaks.json"
                    echo "Gitleaks hisoboti yaratildi."
                '''
            }
        }

        stage('SCA - Dependency-Check') {
            steps {
                sh '''
                    set -eu

                    mkdir -p "$WORKSPACE/reports"

                    test -d "$DEPENDENCY_DATA" || {
                        echo "ERROR: Dependency-Check data papkasi topilmadi."
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

                    echo "Dependency-Check JSON hisoboti yaratildi."
                '''
            }
        }

        stage('Build container') {
            steps {
                sh '''
                    set -eu

                    docker build \
                      -t "$IMAGE_NAME:$BUILD_NUMBER" .

                    echo "Docker image muvaffaqiyatli yaratildi."
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
                    ZAP_REPORT="$WORKSPACE/reports/zap-report.json"

                    cleanup() {
                        docker rm -f "$APP" >/dev/null 2>&1 || true
                        docker network rm "$NET" >/dev/null 2>&1 || true
                        rm -rf "$ZAP_WORK"
                    }

                    # Oldingi qoldiqlarni tozalash
                    cleanup

                    mkdir -p "$WORKSPACE/reports" "$ZAP_WORK"
                    chmod 777 "$ZAP_WORK"

                    # Skript qanday tugashidan qat'i nazar, resurslarni tozalash
                    trap cleanup EXIT

                    docker network create "$NET"

                    docker run -d \
                      --name "$APP" \
                      --network "$NET" \
                      "$IMAGE_NAME:$BUILD_NUMBER"

                    echo "Ilova ishga tushishi uchun kutish..."
                    sleep 5

                    echo "OWASP ZAP skanerlash boshlandi..."

                    # ZAP exit code hisobotni ko'chirishga xalaqit bermasin
                    set +e
                    docker run --rm \
                      --network "$NET" \
                      -v "$ZAP_WORK:/zap/wrk/:rw" \
                      ghcr.io/zaproxy/zaproxy:stable \
                      zap-baseline.py \
                      -t "http://$APP:5000" \
                      -J zap-report.json
                    ZAP_EXIT=$?
                    set -e

                    echo "ZAP exit code: $ZAP_EXIT"

                    echo "ZAP ishchi papkasi:"
                    ls -lah "$ZAP_WORK"

                    # Hisobot yaratilganini tekshirish
                    if [ ! -s "$ZAP_WORK/zap-report.json" ]; then
                        echo "ERROR: ZAP JSON hisoboti yaratilmagan."
                        exit 1
                    fi

                    # Hisobotni Jenkins reports papkasiga saqlash
                    cp "$ZAP_WORK/zap-report.json" "$ZAP_REPORT"

                    test -s "$ZAP_REPORT"

                    # JSON formatini tekshirish
                    python3 -m json.tool "$ZAP_REPORT" > /dev/null

                    echo "OWASP ZAP hisoboti saqlandi: reports/zap-report.json"

                    # ZAP odatiy exit kodlari:
                    # 0 - yangi WARN/FAIL yo'q
                    # 1 - FAIL topilgan
                    # 2 - WARN topilgan
                    # 3 - WARN va FAIL topilgan
                    #
                    # Hisobot avval saqlanadi, keyin build siyosati qo'llanadi.
                    case "$ZAP_EXIT" in
                        0)
                            echo "ZAP: yangi ogohlantirish yoki xato topilmadi."
                            ;;
                        2)
                            echo "ZAP: ogohlantirishlar mavjud. Hisobotni tekshiring."
                            ;;
                        1|3)
                            echo "ERROR: ZAP xavfsizlik xatolarini aniqladi."
                            exit "$ZAP_EXIT"
                            ;;
                        *)
                            echo "ERROR: ZAP kutilmagan exit code qaytardi: $ZAP_EXIT"
                            exit 1
                            ;;
                    esac
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
