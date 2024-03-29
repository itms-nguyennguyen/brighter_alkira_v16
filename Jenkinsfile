pipeline {
    agent none
    stages {
        stage('Checkout') {
            agent {
                label 'syd03'
            }
            steps {
                checkout scm
            }
        }
        stage('Deploy') {
            agent {
                label 'syd03'
            }
            steps {
                script {
                    def mappingFile = readFile '/root/container_directories.txt'
                    def mapping = [:]
                    mappingFile.readLines().each {
                        if (it.contains("Repository") && it.contains("exists in container")) {
                            def parts = it.split(" ")
                            def repo = parts[1]
                            def container = parts[5]
                            if (!mapping.containsKey(repo)) {
                                mapping[repo] = []
                            }
                            mapping[repo].add(container)
                        }
                    }
                    echo "Mapping: ${mapping}"
                    def repoName = sh(script: 'git config --get remote.origin.url | sed "s/.*\\/\\(.*\\)\\.git/\\1/"', returnStdout: true).trim()
                    def targetContainers = mapping[repoName]
                    if (targetContainers) {
                        withCredentials([usernamePassword(credentialsId: 'itms-kainguyen', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                            targetContainers.each { container ->
                                // In ra tên container
                                echo "Deploying to container: ${container} for repository ${repoName}"
                                
                                // Thực thi lệnh trong container
                                sh """
                                    lxc exec ${container} -- bash -c '
                                    cd /opt/odoo/custom/${repoName} && 
                                    git config --global credential.helper store && 
                                    git config user.name ${GIT_USERNAME} && 
                                    git config user.password ${GIT_PASSWORD} &&
                                    git branch --show-current > current_branch.txt &&
                                    git pull origin \$(cat current_branch.txt)'
                                """
                            }
                        }
                    } else {
                        echo "No container to deploy for ${repoName}"
                    }
                }
            }
        }
    }
}
