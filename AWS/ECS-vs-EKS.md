| What Is Amazon Elastic Container Service (ECS)?      | What Is Amazon Elastic Kubernetes Service (EKS)? |
| --------------------------------- | --------------------------------- |
| Amazon Elastic Container Service (Amazon ECS) is a scalable managed service that lets you run and orchestrate a large number of containers. It is not based on Kubernetes.      | Amazon Elastic Kubernetes Service (EKS) lets you run Kubernetes on AWS as a managed service, while retaining compatibility with the open source K8s project.       |
| To run a task, you use a task definition that defines containers. Tasks can be run in a service, which is a configuration that allows you to run and maintain multiple tasks simultaneously in a cluster. Tasks and services can be run via the AWS Fargate service, without having to manage the underlying servers. Alternatively, you can run on Amazon EC2 to gain more control.   | The EKS service sets up and manages the Kubernetes control plane for you. Kubernetes is used to automate the deployment, scaling, and management of your container-based applications.        |
| Amazon ECS allows you to run and stop your containerized applications using simple API calls. You can enjoy standard Amazon EC2 features, as well as gain centralized control over the state of the cluster. | EKS maintains resilience for the Kubernetes control plane by replicating it across multiple Availability Zones. Unhealthy control plane instances are automatically detected and replaced, and version upgrades and patches are also applied automatically. |
| The placement of containers across a cluster can be scheduled according to your isolation policies, resource needs, and availability requirements. Amazon ECS operates your cluster and configuration management systems so you don’t have to handle or scale management infrastructure. | Amazon EKS lets you use existing tooling and plugins from the Kubernetes community. There is full compatibility between Amazon EKS and applications running on other Kubernetes environments. This makes it easy to migrate existing Kubernetes applications to Amazon EKS.|
| Learn more in our detailed guide to [AWS ECS](https://cloud.netapp.com/blog/aws-cvo-blg-aws-ecs-in-depth-architecture-and-deployment-options) | Learn more in our detailed guide to [AWS EKS](https://cloud.netapp.com/blog/aws-cvo-blg-aws-eks-architecture-clusters-nodes-and-networks) architecture |


refer to https://cloud.netapp.com/blog/aws-cvo-blg-aws-ecs-vs-eks-6-key-differences