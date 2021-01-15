@Library('dst-shared@release/shasta-1.4') _

pipeline {

  agent { node { label 'dstbuild' } }

  environment {
    RELEASE_TAG = setReleaseTag()
    PRODUCT="csm"
    TARGET_OS="noos"
    TARGET_ARCH="noarch"
  }

  stages {

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
