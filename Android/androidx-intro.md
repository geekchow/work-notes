# Android X Introduction 


## why we need Android X?

Andorid X is a replacement of Android Support Library.

They are both used to resolve the backward compatible issue.

The scenario is like this:

1. Android API(as libraries) are shipped along with Android OS.
2. With more and more new Android APIs and Android OSs versions release, 
new OSs built in APIs doesn't exist on old OS versions.
3. But We need Adnroid Apps using new APIs could be compitable on old Android OS, 

So we need kinda compatible shim shipped with Android Apps to make them work 
both on new & old OS version.

Android Support Library & Android X are the shims. 

Android Support Library namespace is `android.support.*`

Meanwhile Android X is like
```
implementation 'androidx.appcompat:appcompat:1.0.2'
```


