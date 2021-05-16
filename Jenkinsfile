@Library('dst-shared@master') _

pipeline {

  agent { node { label 'dstbuild' } }

  environment {
    RELEASE_TAG = setReleaseTag()
    PRODUCT="csm"
    TARGET_OS="noos"
    TARGET_ARCH="noarch"
  }

  stages {

    stage('Build Prep') {
      when {expression {return fileExists("runBuildPrep.sh") == true}}
      steps {
          sh "./runBuildPrep.sh"
      }
    }

    stage('Linting') {
      when {expression {return fileExists("runLint.sh") == true}}
      steps {
          sh "./runLint.sh"
      }
    }

    stage('Package') {
      steps {
        packageHelmCharts(chartsPath: "${env.WORKSPACE}/kubernetes",
                          buildResultsPath: "${env.WORKSPACE}/build/results")
      }
    }

    stage('Publish') {
      when { anyOf { branch 'master'; branch 'release/*' } }
      steps {
        publishHelmCharts(chartsPath: "${env.WORKSPACE}/kubernetes")
      }
    }

  }

  post {
    success {
      findAndTransferArtifacts()
    }
  }

}
