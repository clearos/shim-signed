# shim-signed

Forked version of shim-signed with ClearOS changes applied

* git clone git+ssh://git@github.com/clearos/shim-signed.git
* cd shim-signed
* git checkout c7
* git remote add upstream git://git.centos.org/rpms/shim-signed.git
* git pull upstream c7
* git checkout clear7
* git merge --no-commit c7
* git commit
