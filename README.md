# configuration migration

* From msa-dev container under `/opt/fmc_repository/`, clone this project

```
cd /opt/fmc_repository  ; 
```
```
rm -rf /opt/fmc_repository/workflow_configuration_migration
```
```
git clone git@github.com:openmsa/workflow_configuration_migration.git
```

* Create symlink for the currents workflow_configuration_migration workflows, from this project into the MSActivator repository (/opt/fmc_repository/). 

```
cd /opt/fmc_repository/Process; 
```
```
ln -sn ../workflow_configuration_migration workflow_configuration_migration
```
```
chown -R ncuser: /opt/fmc_repository/
```

* From msa-dev container, install required python libraries for configuration migration project (this will install python libs listed on requirements.txt)

```
 /usr/bin/install_repo_deps.sh /opt/fmc_repository/workflow_configuration_migration
```
