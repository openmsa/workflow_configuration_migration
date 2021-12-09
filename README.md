# configuration migration

cd /opt/fmc_repository  ; rm -rf /opt/fmc_repository/workflow_configuration_migration
git clone git@github.com:openmsa/workflow_configuration_migration.git
cd /opt/fmc_repository/Process; ln -sn ../workflow_configuration_migration workflow_configuration_migration
chown -R ncuser: /opt/fmc_repository/
cd /opt/fmc_repository/workflow_configuration_migration

