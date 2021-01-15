# Copyright 2019 Cray Inc. All Rights Reserved.

Name: gitea-crayctldeploy
License: Cray Software License Agreement
Summary: Cray deployment ansible roles for Gitea
Group: System/Management
Version: %(cat .rpm_version)
Release: %(echo ${BUILD_METADATA})
Source: %{name}-%{version}.tar.bz2
Vendor: Cray Inc.
Requires: cray-crayctl
Requires: cray-cmstools-crayctldeploy
Requires: kubernetes-crayctldeploy
Requires: sms-crayctldeploy

# Project level defines TODO: These should be defined in a central location; DST-892
%define afd /opt/cray/crayctl/ansible_framework
%define roles %{afd}/roles
%define playbooks %{afd}/main
%define modules %{afd}/library

%description
A collection of Ansible plays, modules, and roles for Gitea, which provides a
git-based version control system on the Shasta management plane.

%prep
%setup -q

%build

%install
install -m 755 -d %{buildroot}%{playbooks}/
install -m 755 -d %{buildroot}%{roles}/
install -m 755 -d %{buildroot}%{modules}/
install -D -m 644 ansible/library/gitea_org.py %{buildroot}%{modules}/gitea_org.py
install -D -m 644 ansible/library/gitea_repo.py %{buildroot}%{modules}/gitea_repo.py

# All roles and modules from this project
cp -r ansible/roles/* %{buildroot}%{roles}/
cp -r ansible/library/* %{buildroot}%{modules}/

# Install smoke tests under /opt/cray/tests/crayctl-stage4
mkdir -p ${RPM_BUILD_ROOT}/opt/cray/tests/crayctl-stage4/cms/
cp ct-tests/vcs_stage4_ct_tests.sh ${RPM_BUILD_ROOT}/opt/cray/tests/crayctl-stage4/cms/vcs_stage4_ct_tests.sh

%clean
rm -rf %{buildroot}%{roles}/*
rm -f  %{buildroot}%{playbooks}/*
rm -f  %{buildroot}%{library}/*

%files
%defattr(755, root, root)
%dir %{playbooks}
%dir %{modules}
%{modules}/gitea_org.py
%{modules}/gitea_repo.py

%dir %{roles}
%{roles}/vcs_user
%{roles}/vcs_base

/opt/cray/tests/crayctl-stage4/cms/vcs_stage4_ct_tests.sh

