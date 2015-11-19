Name:           shim-signed
Version:        0.9
Release:        2%{?dist}
Summary:        First-stage UEFI bootloader
Provides:	shim = %{version}-%{release}
%define unsigned_release 1.el7

License:        BSD
URL:            http://www.codon.org.uk/~mjg59/shim/
# incorporate mokutil for packaging simplicity
%global mokutil_version 0.2.0
Source0:        https://github.com/lcp/mokutil/archive/mokutil-%{mokutil_version}.tar.gz
Patch0001:	0001-Fix-a-potential-buffer-overflow.patch
Patch0002:	0002-Avoid-a-signed-comparison-error.patch

Source1:	shimx64.efi
Source2:	shimaa64.efi
Source3:	secureboot.cer
Source4:	securebootca.cer
Source5:	BOOT.CSV

%ifarch x86_64
%global efiarch X64
%global efiarchlc x64
%global shimsrc %{SOURCE1}
%endif
%ifarch aarch64
%global efiarch AA64
%global efiarchlc aa64
%global shimsrc %{SOURCE2}
%endif
%define unsigned_dir %{_datadir}/shim/%{efiarchlc}-%{version}-%{unsigned_release}/

BuildRequires: git
BuildRequires: openssl-devel openssl
BuildRequires: pesign >= 0.106-5%{dist}
BuildRequires: efivar-devel
# BuildRequires: shim-unsigned = %{version}-%{unsigned_release}
BuildRequires: shim-unsigned = %{version}-%{unsigned_release}

# for mokutil's configure
BuildRequires: autoconf automake

# Shim uses OpenSSL, but cannot use the system copy as the UEFI ABI is not
# compatible with SysV (there's no red zone under UEFI) and there isn't a
# POSIX-style C library.
# BuildRequires: OpenSSL
Provides: bundled(openssl) = 0.9.8zb

# Shim is only required on platforms implementing the UEFI secure boot
# protocol. The only one of those we currently wish to support is 64-bit x86.
# Adding further platforms will require adding appropriate relocation code.
ExclusiveArch: x86_64 aarch64

%define debug_package \
%ifnarch noarch\
%global __debug_package 1\
%package -n mokutil-debuginfo\
Summary: Debug information for package %{name}\
Group: Development/Debug\
AutoReqProv: 0\
%description -n mokutil-debuginfo\
This package provides debug information for package %{name}.\
Debug information is useful when developing applications that use this\
package or when debugging this package.\
%files -n mokutil-debuginfo -f debugfiles.list\
%defattr(-,root,root)\
%endif\
%{nil}

# Figure out the right file path to use
%global efidir %(eval echo $(grep ^ID= /etc/os-release | sed -e 's/^ID=//' -e 's/rhel/redhat/'))

%define ca_signed_arches x86_64
%define rh_signed_arches x86_64 aarch64

%description
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments. This package contains the version signed by
the UEFI signing service.

%package -n shim
Summary: First-stage UEFI bootloader
Requires: mokutil = %{version}-%{release}
Provides: shim-signed = %{version}-%{release}
Obsoletes: shim-signed < %{version}-%{release}

%description -n shim
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments. This package contains the version signed by
the UEFI signing service.

%package -n mokutil
Summary: Utilities for managing Secure Boot/MoK keys.

%description -n mokutil
Utilities for managing the "Machine's Own Keys" list.

%prep
%setup -T -c -n shim-signed-%{version}
%setup -q -D -a 0 -n shim-signed-%{version} -c
#%%setup -T -D -n shim-signed-%{version}
git init
git config user.email "example@example.com"
git config user.name "rpmbuild -bp"
git add .
git commit -a -q -m "%{version} baseline."
git am --ignore-whitespace %{patches} </dev/null
git config --unset user.email
git config --unset user.name

%build
%define vendor_token_str %{expand:%%{nil}%%{?vendor_token_name:-t "%{vendor_token_name}"}}
%define vendor_cert_str %{expand:%%{!?vendor_cert_nickname:-c "Red Hat Test Certificate"}%%{?vendor_cert_nickname:-c "%%{vendor_cert_nickname}"}}

%ifarch %{ca_signed_arches}
pesign -i %{shimsrc} -h -P > shim.hash
if ! cmp shim.hash %{unsigned_dir}shim.hash ; then
	echo Invalid signature\! > /dev/stderr
	exit 1
fi
cp %{shimsrc} shim.efi
%endif
%ifarch %{rh_signed_arches}
%pesign -s -i %{unsigned_dir}shim.efi -a %{SOURCE4} -c %{SOURCE3} -n redhatsecureboot301 -o shim-%{efidir}.efi
%endif
%ifarch %{rh_signed_arches}
%ifnarch %{ca_signed_arches}
cp shim-%{efidir}.efi shim.efi
%endif
%endif

%pesign -s -i %{unsigned_dir}MokManager.efi -o MokManager.efi -a %{SOURCE4} -c %{SOURCE3} -n redhatsecureboot301
%pesign -s -i %{unsigned_dir}fallback.efi -o fallback.efi -a %{SOURCE4} -c %{SOURCE3} -n redhatsecureboot301

cd mokutil-%{mokutil_version}
./autogen.sh
%configure
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
install -D -d -m 0755 $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/
install -m 0644 shim.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shim.efi
install -m 0644 shim-%{efidir}.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shim-%{efidir}.efi
install -m 0644 MokManager.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/MokManager.efi
install -m 0644 %{SOURCE5} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/BOOT.CSV

install -D -d -m 0755 $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/
install -m 0644 shim.efi $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/BOOT%{efiarch}.EFI
install -m 0644 fallback.efi $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/fallback.efi

cd mokutil-%{mokutil_version}
make PREFIX=%{_prefix} LIBDIR=%{_libdir} DESTDIR=%{buildroot} install

%files -n shim
/boot/efi/EFI/%{efidir}/shim.efi
/boot/efi/EFI/%{efidir}/shim-%{efidir}.efi
/boot/efi/EFI/%{efidir}/MokManager.efi
/boot/efi/EFI/%{efidir}/BOOT.CSV
/boot/efi/EFI/BOOT/BOOT%{efiarch}.EFI
/boot/efi/EFI/BOOT/fallback.efi

%files -n mokutil
%{!?_licensedir:%global license %%doc}
%license mokutil-%{mokutil_version}/COPYING
%doc mokutil-%{mokutil_version}/README
%{_bindir}/mokutil
%{_mandir}/man1/*

%changelog
* Mon Jul 20 2015 Peter Jones <pjones@redhat.com> - 0.9-2
- Apparently I'm *never* going to learn to build this in the right target
  the first time through.
  Related: rhbz#1100048

* Mon Jun 29 2015 Peter Jones <pjones@redhat.com> - 0.9-0.1
- Bump version for 0.9
  Also use mokutil-0.3.0
  Related: rhbz#1100048

* Tue Jun 23 2015 Peter Jones <pjones@redhat.com> - 0.7-14.1
- Fix mokutil_version usage.
  Related: rhbz#1100048

* Mon Jun 22 2015 Peter Jones <pjones@redhat.com> - 0.7-14
- Pull in aarch64 build so they can compose that tree.
  (-14 to match -unsigned)
  Related: rhbz#1100048

* Wed Feb 25 2015 Peter Jones <pjones@redhat.com> - 0.7-12
- Fix some minor build bugs on Aarch64
  Related: rhbz#1190191

* Tue Feb 24 2015 Peter Jones <pjones@redhat.com> - 0.7-11
- Fix section loading on Aarch64
  Related: rhbz#1190191

* Wed Dec 17 2014 Peter Jones <pjones@redhat.com> - 0.7-10
- Rebuild for Aarch64 to get \EFI\BOOT\BOOTAA64.EFI named right.
  (I managed to fix the inputs but not the outputs in -9.)
  Related: rhbz#1100048

* Wed Dec 17 2014 Peter Jones <pjones@redhat.com> - 0.7-9
- Rebuild for Aarch64 to get \EFI\BOOT\BOOTAA64.EFI named right.
  Related: rhbz#1100048

* Tue Oct 21 2014 Peter Jones <pjones@redhat.com> - 0.7-8
- Build for aarch64 as well 
  Related: rhbz#1100048
- out-of-bounds memory read flaw in DHCPv6 packet processing
  Resolves: CVE-2014-3675
- heap-based buffer overflow flaw in IPv6 address parsing
  Resolves: CVE-2014-3676
- memory corruption flaw when processing Machine Owner Keys (MOKs)
  Resolves: CVE-2014-3677

* Tue Sep 23 2014 Peter Jones <pjones@redhat.com> - 0.7-7
- Make sure we use the right keys on Aarch64.
  (It's only a demo at this stage.)
  Related: rhbz#1100048

* Tue Sep 23 2014 Peter Jones <pjones@redhat.com> - 0.7-6
- Add ARM Aarch64.
  Related: rhbz#1100048

* Thu Feb 27 2014 Peter Jones <pjones@redhat.com> - 0.7-5.2
- Get the right signatures on shim-redhat.efi
  Related: rhbz#1064449

* Thu Feb 27 2014 Peter Jones <pjones@redhat.com> - 0.7-5.1
- Update for signed shim for RHEL 7
  Resolves: rhbz#1064449

* Thu Nov 21 2013 Peter Jones <pjones@redhat.com> - 0.7-5
- Fix shim-unsigned deps.
  Related: rhbz#1032583

* Thu Nov 21 2013 Peter Jones <pjones@redhat.com> - 0.7-4
- Make dhcp4 work better.
  Related: rhbz#1032583

* Thu Nov 14 2013 Peter Jones <pjones@redhat.com> - 0.7-3
- Make lockdown include UEFI and other KEK/DB entries.
  Related: rhbz#1030492

* Fri Nov 08 2013 Peter Jones <pjones@redhat.com> - 0.7-2
- Handle SetupMode better in lockdown as well
  Related: rhbz#996863

* Wed Nov 06 2013 Peter Jones <pjones@redhat.com> - 0.7-1
- Don't treat SetupMode variable's presence as meaning we're in SetupMode.
  Related: rhbz#996863

* Wed Nov 06 2013 Peter Jones <pjones@redhat.com> - 0.6-3
- Use the correct CA and signer certificates.
  Related: rhbz#996863

* Thu Oct 31 2013 Peter Jones <pjones@redhat.com> - 0.6-1
- Update to 0.6-1
  Resolves: rhbz#1008379

* Wed Aug 07 2013 Peter Jones <pjones@redhat.com> - 0.4-3.2
- Depend on newer pesign.
  Related: rhbz#989442

* Tue Aug 06 2013 Peter Jones <pjones@redhat.com> - 0.4-3.1
- Rebuild with newer pesign
  Related: rhbz#989442

* Tue Aug 06 2013 Peter Jones <pjones@redhat.com> - 0.4-3
- Update for RHEL signing with early test keys.
  Related: rhbz#989442

* Thu Jun 20 2013 Peter Jones <pjones@redhat.com> - 0.4-1
- Provide a fallback for uninitialized Boot#### and BootOrder
  Resolves: rhbz#963359
- Move all signing from shim-unsigned to here
- properly compare our generated hash from shim-unsigned with the hash of
  the signed binary (as opposed to doing it manually)

* Fri May 31 2013 Peter Jones <pjones@redhat.com> - 0.2-4.4
- Re-sign to get alignments that match the new specification.
  Resolves: rhbz#963361

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2-4.3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Jan 02 2013 Peter Jones <pjones@redhat.com> - 0.2-3.3
- Add obsoletes and provides for earlier shim-signed packages, to cover
  the package update cases where previous versions were installed.
  Related: rhbz#888026

* Mon Dec 17 2012 Peter Jones <pjones@redhat.com> - 0.2-3.2
- Make the shim-unsigned dep be on the subpackage.

* Sun Dec 16 2012 Peter Jones <pjones@redhat.com> - 0.2-3.1
- Rebuild to provide "shim" package directly instead of just as a Provides:

* Sat Dec 15 2012 Peter Jones <pjones@redhat.com> - 0.2-3
- Also provide shim-fedora.efi, signed only by the fedora signer.
- Fix the fedora signature on the result to actually be correct.
- Update for shim-unsigned 0.2-3

* Mon Dec 03 2012 Peter Jones <pjones@redhat.com> - 0.2-2
- Initial build
