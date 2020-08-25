# How to build a jenkins plugin?

## mvn preparation
> Before you start you need to update the settings.xml file of your local Maven installation this way:

- 1) Add a mirror to the mirrors list for the Jenkins Update Centre:
```xml
<mirrors>
...
    <mirror>
      <id>repo.jenkins-ci.org</id>
      <url>http://repo.jenkins-ci.org/public/</url>
      <mirrorOf>m.g.o-public</mirrorOf>
    </mirror>
...
</mirrors>
```

- 2) Add a profile for Jenkins to the profiles list:
```xml
<profiles>
...
<profile>
      <id>jenkins</id>
      <activation>
        <activeByDefault>true</activeByDefault>
      </activation>
      <repositories>
        <repository>
          <id>repo.jenkins-ci.org</id>
          <url>http://repo.jenkins-ci.org/public/</url>
        </repository>
      </repositories>
      <pluginRepositories>
        <pluginRepository>
          <id>repo.jenkins-ci.org</id>
          <url>http://repo.jenkins-ci.org/public/</url>
        </pluginRepository>
      </pluginRepositories>
    </profile>
...
</profiles>
```

Step 1: Create the Plugin Structure
```shell
 # refer to: https://wiki.jenkins.io/display/JENKINS/Plugin+tutorial#Plugintutorial-CreatingaNewPlugin
 mvn archetype:generate -Dfilter=io.jenkins.archetypes:empty-plugin
```



## Build Plugins

`mvn package`

`mvn install` 

references
https://www.jenkins.io/blog/2017/08/07/intro-to-plugin-development/