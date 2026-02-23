
kubectl run tmp --restart=Never -i --rm --image=busybox -- curl www.baidu.com


kubectl -n moon exec secret-handler -- find /tmp/secret2 
