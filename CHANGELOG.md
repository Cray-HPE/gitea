# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Disabled concurrent Jenkins builds on same branch/commit
- Added build timeout to avoid hung builds

### Dependencies
- CASMCMS-9011: Bump `cray-keycloak-setup` version from 3.6.1 to 3.7.X; use `update_external_versions` to find latest 3.7.X version

## [2.6.3] - 2023-05-17

### Fixed

- CASMPET-6571 - Fixed incorrect POSTGRES_HOST value.

## [2.6.2] - 2023-05-03

### Changed

- CASMCMS-7594 - Added the CMN gateway to both virtual services.

## [2.6.1] - 2023-04-06

### Changed

- CASMCMS-8512 - Fix typo in Chart that causes logical DB backups to be disabled.

## [2.6.0] - 2023-03-23

### Changed

- CASMCMS-8457 - Update chart to use new postgres operator

## [2.5.3] - 2023-1-27

### Fixed

- Fixed reverse proxy authentication

## [2.5.2] - 2022-12-20

### Added

- Add Artifactory authentication to Jenkinsfile

## [2.5.0] - 2022-08-22

### Changed

- CASMINST-5250 - fix gitea user creation to handle passwords with leading '-'
- CASMPET-5864 - update keycloak-setup default image version.
