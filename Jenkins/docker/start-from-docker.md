

```shell
# pull the jenkins image to local.
docker pull jenkins/jenkins:jdk11

# run the container
docker run -p 8080:8080 -p 50000:50000 -v ~/jenkins_home:/var/jenkins_home jenkins/jenkins:jdk11
```


https://hub.docker.com/_/jenkins
https://github.com/jenkinsci/docker