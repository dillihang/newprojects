from capstoneCICD import SSHClientManager, RemoteDockerDeployer, CDPipeline

container_name = "test-app-container"

# Connect to remote
ssh_client = SSHClientManager()
ssh_client.connect()

# Deployer points to an image that's already on the host
deployer = RemoteDockerDeployer(ssh_client, container_name)

# CDPipeline with image already on remote, so no pull
cd_pipeline = CDPipeline(deployer=deployer, pull_image="dillihanglimbu/finaltest-app:latest")

# Only run log fetching step
cd_pipeline.logs_step()

# Disconnect after test
ssh_client.disconnect()