import docker
import os
import requests
from getpass import getpass
from datetime import datetime
import time
import paramiko
from dotenv import load_dotenv

load_dotenv()

class DockerImageBuilder:
    def __init__(self, dockerfile_path:str, image_name:str, image_tag:str = None, build_context = None):
        self.__docker_client = docker.from_env()

        try:
            self.__docker_client.ping()
        except:
            raise ConnectionError("Cannot connect to Docker daemon")

        if not os.path.exists(dockerfile_path):
            raise FileNotFoundError(f"Dockerfile not found: {dockerfile_path}")
        
        if not os.path.isfile(dockerfile_path):
            raise ValueError(f"Path is not a file: {dockerfile_path}")

        self.__dockerfile_path = dockerfile_path
        self.__image_name = image_name
        if image_tag is None:
            tag_timestamp = f"{datetime.now().strftime("%Y%m%d-%H%M%S")}"
            self.__image_tag = tag_timestamp
        else:
            self.__image_tag = image_tag 
        if build_context is None:
            self.__build_context = os.path.dirname(dockerfile_path)
        else:
            self.__build_context = build_context
    
    def image_exists(self):
        full_name = f"{self.__image_name}:{self.__image_tag}"
        try:
            self.__docker_client.images.get(full_name)
            return True
        except Exception:
            return False
        
    def rename_on_failure(self):
        try:
            old_name = f"{self.__image_name}:{self.__image_tag}"
            image = self.__docker_client.images.get(old_name)
            new_tag = f"{self.__image_tag}-failed"
            image.tag(self.__image_name, tag=new_tag)
            print(f"[BUILDER] Rename success {self.__image_name}:{new_tag}")
            return True
        except Exception as e:
            print(f"[BUILDER ERROR] Rename failed: {e}")
            return False
    
    def build_image(self):
        try:
            image, logs = self.__docker_client.images.build(
                path=self.__build_context,
                dockerfile=self.__dockerfile_path,
                tag=f"{self.__image_name}:{self.__image_tag}",
                rm=True,
                nocache=True
            )
            print(f"[BUILDER] Image {image.id[:12]} built successfully")
            return image
        except Exception as e:
            print(f"[BUILDER ERROR] Build failed: {e}")
            return None
    
    def get_name_with_tag(self):
        return f"{self.__image_name}:{self.__image_tag}"

class DockerContainerRunner:
    def __init__(self, image):
        self.__docker_client = docker.from_env()
        self.__docker_image = image
        self.__container = None
    
    def start_container(self):
        try:
            self.__container = self.__docker_client.containers.run(
                image=self.__docker_image,
                detach=True,
                remove=False
            )
            time.sleep(3)

            self.__container.reload()

            if self.__container.status == "exited":
                exit_code = self.__container.attrs["State"]["ExitCode"]
                logs = self.__container.logs()

                if exit_code == 0:
                    print(f"[RUNNER] Script completed successfully")
                    return True
                else:
                    print(f"[RUNNER ERROR] Script failed (exit {exit_code}) - {logs}")
                    return False
            else:
                print(f"[RUNNER] Container running (status: {self.__container.status})")
                return True
            
        except Exception as e:
            print(f"[RUNNER ERROR] Starting container failed: {e}")
            self.__container = None
            return False
    
    def stop_container(self):
        if not self.__container:
            print("[RUNNER WARN] No container initialized")
            return False
        
        try:
            self.__container.reload()
            if self.__container.status == "running":
                self.__container.stop()
                print(f"[RUNNER] Container stopped")
                return True
            else:
                print(f"[RUNNER INFO] Container not running (status: {self.__container.status})")
                return True
        except Exception as e:
            print(f"[RUNNER ERROR] Container stop failed: {e}")
            return False

    def remove_container(self):
        if not self.__container:
            print("[RUNNER WARN] No container initialized")
            return False
        
        try:
            self.__container.reload()
            if self.__container.status == "exited":
                self.__container.remove()
                print(f"[RUNNER] Container removed")
                return True
            else:
                print(f"[RUNNER WARN] Container status {self.__container.status}, cannot remove")
                return False
        except Exception as e:
            print(f"[RUNNER ERROR] Could not remove container: {e}")
            return False

class CIPipeLine():
    def __init__(self, builder: "DockerImageBuilder"):
        self.__builder = builder
        self.__runner = None
        self.__image = None
        self.__adhoc_test = None
        self.__status = True
        self.__docker_registry_client = None

    def set_test(self, test_func):
        self.__adhoc_test = test_func
    
    def set_registry_client(self, docker_registry_client):
        self.__docker_registry_client = docker_registry_client

    def build_step(self):
        if self.__builder.image_exists():
            print(f"[CI ERROR] Image already exists")
            return False
        
        self.__image = self.__builder.build_image()
        return self.__image is not None
    
    def run_step(self):
        if not self.__image:
            print(f"[CI ERROR] No image available")
            return False
        
        self.__runner = DockerContainerRunner(image=self.__image)
        return self.__runner.start_container()
    
    def test_step(self):
        if not self.__adhoc_test:
            print(f"[CI] No test provided")
            return True
        
        try:
            time.sleep(3)
            result = self.__adhoc_test()
            return result
        except Exception as e:
            print(f"[CI ERROR] Test execution error: {e}")
            return False

    def stop_step(self):
        if self.__runner:
            return self.__runner.stop_container()
        return True

    def remove_step(self):
        if self.__runner:
            return self.__runner.remove_container()
        return True
    
    def mark_failed_build(self):
        if self.__builder:
            self.__builder.rename_on_failure()
        
    def push_step(self, push_latest=False):
        if not self.__docker_registry_client:
            print("[CI] No registry client set, skipping push")
            return True

        if not self.__docker_registry_client.push_to_registry(self.__image, push_latest=push_latest):
            print(f"[CI ERROR] Push to registry failed")
            return False
        return True
    
    import docker

    def cleanup_local_image(self):
        if not self.__image:
            return True 

        try:
            client = docker.from_env()
            full_name = self.__image.tags[0]
            client.images.remove(image=full_name, force=True)
            print(f"[CI] Cleaned up local image {full_name}")
            return True
        except Exception as e:
            print(f"[CI WARN] Could not remove local image: {e}")
            return False


    def execute(self, push_latest=False):
        print("=" * 50)
        print("[CI] Starting CI Pipeline")
        print("=" * 50)
        
        steps = [
            ("Build", self.build_step),
            ("Run", self.run_step),
            ("Test", self.test_step),
            ("Push", lambda: self.push_step(push_latest=push_latest))
        ]
        
        for step_name, step_func in steps:
            print(f"\n[CI] {step_name} step...")
            if not step_func():
                print(f"[CI ERROR] Failed at {step_name} step")
                self.__status = False
                break
        
        print(f"\n[CI] Cleanup step...")
        self.stop_step()
        self.remove_step()

        if not self.__status:
            self.mark_failed_build()
            print("\n" + "=" * 50)
            print("[CI FAILED] Pipeline failed!")
            print("=" * 50)
            return False
        else:
            self.cleanup_local_image()
            print("\n" + "=" * 50)
            print("[CI SUCCESS] Pipeline completed!")
            print("=" * 50)
            return True  

    def get_status(self):
        return self.__status

class DockerRegistryClient():
    def __init__(self):
        self.__registry_url = os.getenv("DOCKER_REGISTRY_URL", "docker.io")
        self.__docker_client = docker.from_env()
        self.__namespace = os.getenv("DOCKER_NAMESPACE") or os.getenv("DOCKER_USERNAME")
        self.__pushed_image = None
        self.__pulled_image = None

        self._auto_login()

    def _auto_login(self):

        username = os.getenv("DOCKER_USERNAME")
        password = os.getenv("DOCKER_PASSWORD")

        if not all([username, password]):
            print("[WARNING] DOCKER_USERNAME or DOCKER_PASSWORD not set in .env")
            print("[INFO] Public pulls will work, private pushes may fail")
            return False
    
        try:
            self.__docker_client.login(
                username=username,
                password=password,
                registry=self.__registry_url
            )
            print(f"[INFO] Auto-logged in as {username}")
            return True
        except Exception as e:
            print(f"[ERROR] Auto-login failed - {e}")
            return False
    
    def name_extractor(self, image_obj):
        image_name_only = None
        try:
            image_name_only = image_obj.tags[0].split(":")[0]
            return image_name_only
        except Exception as e:
            print(f"[ERROR] Failed to extract name {e}")
            return image_name_only
    
    def tag_extractor(self, image_obj):
        image_tag_only = None
        try:
            image_tag_only = image_obj.tags[0].split(":")[1]
            return image_tag_only
        except Exception as e:
            print(f"[ERROR] Failder to extract tag {e}")
    
    def _push(self, full_repo_name: str):
        try:
            print(f"[PUSHING] {full_repo_name}")
            response=self.__docker_client.images.push(
                repository=full_repo_name,
                stream=True,
                decode=True
            )
            for line in response:
                if 'error' in line:
                    print(f"[ERROR] Push failed: {line['error']}")
                    return False
            print(f"[INFO] Push complete")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to push - {e}")
            return False

    def _build_full_name(self, name, tag, namespace):

        if self.__registry_url in ["docker.io", "index.docker.io", ""]:
            return f"{namespace}/{name}:{tag}"
        else:
            return f"{self.__registry_url}/{namespace}/{name}:{tag}"
    
    def _tag_image(self, image_obj, namespace:str, img_name:str, img_tag:str):
        target = f"{namespace}/{img_name}:{img_tag}"
        try:
            image_obj.tag(target)
            print(f"[TAGGED] {target}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to tag {target}: {e}")
            return False

    def push_to_registry(self, image_obj, repo_namespace: str = None, push_latest=False):
        print(f"[INFO] Starting push to registry")
        
        if not self.__namespace:
            print("[ERROR] No namespace configured")
            return False
        
        img_name = self.name_extractor(image_obj)
        img_tag = self.tag_extractor(image_obj)

        if not all([img_name, img_tag]):
            print("[ERROR] Could not resolve image name or tag")
            return False
        
        namespace = repo_namespace or self.__namespace

        if not self._tag_image(image_obj, namespace, img_name, img_tag):
            return False
        
        full_name = self._build_full_name(img_name, img_tag, namespace)
        if not self._push(full_name):
            return False
        
        self.__pushed_image = full_name
        
        if push_latest:
            if not self._tag_image(image_obj, namespace, img_name, img_tag="latest"):
                return False

            latest_name = self._build_full_name(img_name, "latest", namespace)
            if not self._push(latest_name):
                return False
        
        return True
    
    def pull(self, repo: str = None):
        pull_repo = repo or self.__pushed_image
        
        if not pull_repo:
            print("[ERROR] No repository specified")
            return False
        
        try:
            self.__pulled_image = self.__docker_client.images.pull(pull_repo)
            print(f"[PULLED] {pull_repo}")
            return True
        except Exception as e:
            print(f"[ERROR] Pull failed - {e}")
            return False
        
    def get_pulled_image(self):
        return self.__pulled_image
    
    def get_pushed_image_name(self):
        return self.__pushed_image

class SSHClientManager():
    def __init__(self):
        self.__client = None
        self.__connected = False
        
        self.__host = os.getenv("REMOTE_HOST")
        self.__username = os.getenv("REMOTE_USER")
        self.__key_path = os.getenv("SSH_KEY_PATH")

        if not self.__host:
            raise ValueError("REMOTE_HOST must be set in .env file")
        if not self.__username:
            raise ValueError("REMOTE_USER must be set in .env file")
        if not self.__key_path:
            raise ValueError("SSH_KEY_PATH must be set in .env file")
        
        if not os.path.exists(self.__key_path):
            raise FileExistsError(f"SSH key not found: {self.__key_path}")
        
        print(f"[SSH] Config: {self.__username}@{self.__host}")

    def connect(self):
        if self.__connected:
            return True
        
        try:
            self.__client = paramiko.SSHClient()
            self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy)

            self.__client.connect(hostname=self.__host, username=self.__username, key_filename=self.__key_path)

            self.__connected = True
            print(f"Connection Established")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
        
    def execute_command(self, command):

        if not self.__connected:
            self.connect()

        stdin, stdout, stderr = self.__client.exec_command(command=command, get_pty=True)
        exit_status = stdout.channel.recv_exit_status()

        return stdout.read().decode(), stderr.read().decode(), exit_status
    
    def disconnect(self):

        if self.__client:
            self.__client.close()
            self.__client = None
            self.__connected = False

class RemoteDockerDeployer():
    def __init__(self, ssh_client, container_name: str):
        self.__ssh_client = ssh_client
        self.__pulled_image = None
        self.__existing_container = container_name

        print(f"[DEPLOYER] Initialized for container: {self.__existing_container}")
        if not self._docker_login():
            raise ValueError("[DEPLOYER ERROR] Docker login failed. Check .env credentials")

    def _docker_login(self):
        username = os.getenv("DOCKER_USERNAME")
        password = os.getenv("DOCKER_PASSWORD")
        
        if not all([username, password]):
            print("[DEPLOYER ERROR] DOCKER_USERNAME or DOCKER_PASSWORD not set in .env")
            return False
    
        cmd = f"echo '{password}' | docker login -u '{username}' --password-stdin"
        out, err, code = self.__ssh_client.execute_command(cmd)
        
        if code != 0:
            print(f"[DEPLOYER ERROR] Docker login failed on remote: {err.strip()}")
            return False
        
        print(f"[DEPLOYER] Docker login successful as {username}")
        return True

    def pull_image(self, image_name: str):
        if not image_name:
            print("[DEPLOYER WARN] No image specified to pull")
            return False

        cmd = f"docker pull {image_name}"
        out, err, code = self.__ssh_client.execute_command(cmd)
        
        if code != 0:
            print(f"[DEPLOYER ERROR] Failed to pull image '{image_name}': {err.strip()}")
            return False

        print(f"[DEPLOYER] Successfully pulled image '{image_name}'")
        self.__pulled_image = image_name
        return True

    def stop_existing_container(self):
        if not self.__existing_container:
            print("[DEPLOYER WARN] No container name specified to stop")
            return True  # nothing to stop

        cmd = f"docker rm -f {self.__existing_container} 2>/dev/null || true"
        out, err, code = self.__ssh_client.execute_command(cmd)
        
        if code == 0:
            print(f"[DEPLOYER] Stopped and removed existing container '{self.__existing_container}'")
            return True
        else:
            print(f"[DEPLOYER WARN] Could not stop container '{self.__existing_container}': {err.strip()}")
            return False

    def run_new_container(self):
        if not self.__pulled_image:
            print("[DEPLOYER ERROR] No image pulled to run")
            return False

        cmd = f"docker run -d --name {self.__existing_container} {self.__pulled_image}"
        out, err, code = self.__ssh_client.execute_command(cmd)
        
        if code != 0:
            print(f"[DEPLOYER ERROR] Failed to start container '{self.__existing_container}': {err.strip()}")
            return False
        
        print(f"[DEPLOYER] Container '{self.__existing_container}' started successfully with image '{self.__pulled_image}'")
        return True

    def fetch_logs(self, max_retries=5, delay=1):
        if not self.__existing_container:
            print("[DEPLOYER WARN] No container specified to fetch logs")
            return None

        out = None
        for attempt in range(max_retries):
            out, err, code = self.__ssh_client.execute_command(f"docker logs {self.__existing_container}")
            if out.strip():  # if there’s any output
                break
            print(f"[DEPLOYER INFO] Logs empty, retrying ({attempt+1}/{max_retries})...")
            time.sleep(delay)
        
        if code != 0:
            print(f"[DEPLOYER ERROR] Could not fetch logs: {err.strip()}")
            return None

        print(f"[DEPLOYER] Retrieved logs for container '{self.__existing_container}'")
        return out
    
class CDPipeline():
    def __init__(self, deployer: "RemoteDockerDeployer", pull_image: str = None, registry_client: "DockerRegistryClient" = None):
        self.__deployer = deployer
        self.__image_to_deploy = pull_image
        self.__registry_client = registry_client
        self.__status = True

    def pull_step(self):
        if not self.__image_to_deploy:
            # ask registry for latest image if registry client is set
            if self.__registry_client:
                self.__image_to_deploy = self.__registry_client.get_pushed_image_name()
            if not self.__image_to_deploy:
                print("[CD] No image specified for deployment, skipping pull")
                return True

        print(f"[CD] Pulling image {self.__image_to_deploy}")
        return self.__deployer.pull_image(self.__image_to_deploy)

    def stop_step(self):
        print("[CD] Stopping existing container...")
        return self.__deployer.stop_existing_container()

    def run_step(self):
        print("[CD] Running new container...")
        return self.__deployer.run_new_container()

    def logs_step(self):
        import time
        time.sleep(3)  # wait a bit to let container produce logs
        logs = self.__deployer.fetch_logs()
        if logs is not None:
            print(f"[CD] Container logs:\n{logs}")
            return True
        return False

    def cleanup_local_image(self):
        if not self.__image_to_deploy:
            return True  # nothing to clean

        try:
            client = docker.from_env()
            # Remove the specific tag pulled
            print(f"[CD] Removing local image {self.__image_to_deploy}")
            client.images.remove(image=self.__image_to_deploy, force=True)

            # Optionally also remove 'latest' if it exists
            if ":latest" not in self.__image_to_deploy:
                latest_tag = self.__image_to_deploy.split(":")[0] + ":latest"
                try:
                    client.images.remove(image=latest_tag, force=True)
                    print(f"[CD] Removed local 'latest' tag {latest_tag}")
                except Exception:
                    pass  # ignore if latest tag doesn't exist
            return True
        except Exception as e:
            print(f"[CD WARN] Could not remove local image: {e}")
            return False

    def execute(self):
        print("=" * 50)
        print("[CD] Starting CD Pipeline")
        print("=" * 50)

        steps = [
            ("Pull Image", self.pull_step),
            ("Stop Existing Container", self.stop_step),
            ("Run New Container", self.run_step)
        ]

        for step_name, step_func in steps:
            print(f"\n[CD] {step_name} step...")
            if not step_func():
                print(f"[CD ERROR] Failed at {step_name} step")
                self.__status = False
                break
        
        print(f"\n[CD] Fetch logs step...")
        self.logs_step()  # always attempt logs, does not fail pipeline

        print(f"\n[CD] Clean up step...")
        self.cleanup_local_image()

        if self.__status:
            print("\n" + "=" * 50)
            print("[CD SUCCESS] Pipeline completed!")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("[CD FAILED] Pipeline failed!")
            print("=" * 50)
        
        return self.__status


class Orchestrator:
    def __init__(self, ci_pipeline: "CIPipeLine", cd_pipeline: "CDPipeline" = None):
        self.ci_pipeline = ci_pipeline
        self.cd_pipeline = cd_pipeline
        self.status = {"CI": None, "CD": None}

    def execute(self, run_ci=True, run_cd=True, skip_tests=False, push=False, push_latest=False):
        print("=" * 60)
        print("[ORCHESTRATOR] Starting full pipeline")
        print("=" * 60)

        # --- CI Phase ---
        ci_result = None
        if run_ci:
            print("\n[ORCHESTRATOR] Running CI pipeline...")
            if skip_tests:
                self.ci_pipeline.set_test(None)

            ci_result = self.ci_pipeline.execute(push_latest=push_latest if push else False)
            self.status["CI"] = ci_result

            if not ci_result:
                print("\n[ORCHESTRATOR] CI failed, aborting deployment")
                return self.status
        else:
            print("[ORCHESTRATOR] CI skipped")
            self.status["CI"] = "Skipped"

        # --- CD Phase ---
        if run_cd and self.cd_pipeline:
            print("\n[ORCHESTRATOR] Running CD pipeline...")
            cd_result = self.cd_pipeline.execute()
            self.status["CD"] = cd_result
        else:
            print("[ORCHESTRATOR] CD skipped")
            self.status["CD"] = "Skipped"

        # --- Summary ---
        print("\n" + "=" * 60)
        print("[ORCHESTRATOR] Pipeline summary:")
        for phase, result in self.status.items():
            print(f"  {phase}: {result}")
        print("=" * 60)

        return self.status



if __name__ == "__main__":
    docker_path = r"C:\Users\44746\Documents\Python\Newprojects\Devopsandcloudautomation\devopsEx31\Dockerfile"
    container_name = "test-app-container"  # remote container name
    
    print("\n" + "=" * 60)
    print("FULL PIPELINE TEST: CI -> CD (with latest push)")
    print("=" * 60)
    
    try:
        # -------------------
        # 1️⃣ CI Setup
        # -------------------
        registry = DockerRegistryClient()
        builder = DockerImageBuilder(dockerfile_path=docker_path, image_name="finaltest-app")
        ci_pipeline = CIPipeLine(builder=builder)
        ci_pipeline.set_registry_client(registry)
        
        # -------------------
        # 2️⃣ CD Setup
        # -------------------
        ssh_client = SSHClientManager()
        ssh_client.connect()
        deployer = RemoteDockerDeployer(ssh_client=ssh_client, container_name=container_name)
        cd_pipeline = CDPipeline(deployer=deployer, registry_client=registry)  # image=None, CD decides
        
        # -------------------
        # 3️⃣ Orchestrator Setup
        # -------------------
        orchestrator = Orchestrator(ci_pipeline=ci_pipeline, cd_pipeline=cd_pipeline)
        
        # -------------------
        # 4️⃣ Execute Full Pipeline
        # -------------------
        status = orchestrator.execute(run_ci=True, run_cd=True, skip_tests=False, push=True, push_latest=True)
        
        print("\nFINAL PIPELINE STATUS:", status)
        
        # -------------------
        # 5️⃣ Disconnect SSH
        # -------------------
        ssh_client.disconnect()
        
    except Exception as e:
        print(f"[PIPELINE ERROR] {e}")
