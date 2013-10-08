%define modulename rtlib

Name: rtfetch
Version: 20131007
Release: alt1

Summary: The set of tools to organize and management of your torrents

Group: File tools
License: GPLv3
Url: http://github.com/mdevaev/rtfetch.git

Packager: Vitaly Lipatov <lav@altlinux.ru>

# http://web.archive.org/web/20060623094750/http://homepages.nildram.co.uk/~kial/evhz.c
# Source-git: https://gist.github.com/993351
Source: %name-%version.tar

BuildArch: noarch

%setup_python_module %modulename
#BuildRdepends=('python2' 'python2-bencode' 'python2-ulib-git')

%description
The set of tools to organize and management of your torrents.

%prep
%setup

%build
%python_build

%install
%python_install
for i in rtfetch rtquery rtload rtfile rtdiff ; do
    mv %buildroot%_bindir/$i.py %buildroot%_bindir/$i
done
#mv $pkgdir/usr/bin/rthook-manage-trackers.py $pkgdir/usr/bin/rthook-manage-trackers

%files
%_bindir/rt*
%python_sitelibdir/%modulename/
#%python_sitelibdir/%modulename-%version-*.egg-info

%changelog
* Tue Oct 08 2013 Vitaly Lipatov <lav@altlinux.ru> 20131007-alt1
- initial build for ALT Linux Sisyphus
